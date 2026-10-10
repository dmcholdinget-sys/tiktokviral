from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers, viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import *
from .services import review, assign, transition, publish, audit, safe_url
from .providers import CandidateRecordSerializer, ingest, run_discovery


class StaffOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_staff


class CandidateSerializer(serializers.ModelSerializer):
    score_label = serializers.ReadOnlyField()

    class Meta:
        model = VideoCandidate
        fields = "__all__"


class AssignmentSerializer(serializers.ModelSerializer):
    candidate_title = serializers.CharField(source="candidate.title", read_only=True)
    candidate_url = serializers.CharField(source="candidate.url", read_only=True)
    publisher_name = serializers.CharField(
        source="publisher.display_name", read_only=True
    )

    class Meta:
        model = DistributionAssignment
        fields = "__all__"


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = PublishedPost
        fields = "__all__"


class MetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerformanceSnapshot
        fields = "__all__"
        read_only_fields = ["id", "entered_by", "verified", "source"]

    def validate_observed_at(self, value):
        if value > timezone.now():
            raise serializers.ValidationError("Observation cannot be in the future.")
        return value

    def validate(self, data):
        if not any(
            data.get(k) is not None
            for k in ("views", "likes", "comments", "shares", "followers_gained")
        ):
            raise serializers.ValidationError("Supply at least one observed metric.")
        if data.get("observed_at") and data["observed_at"] < data["post"].published_at:
            raise serializers.ValidationError("Observation precedes publication.")
        return data


def operation(call):
    try:
        return call()
    except DjangoValidationError as exc:
        raise serializers.ValidationError(exc.messages)
    except IntegrityError:
        raise serializers.ValidationError("A duplicate record already exists.")


class CandidateViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CandidateSerializer

    def get_queryset(self):
        qs = VideoCandidate.objects.all()
        if (
            not self.request.user.is_staff
            and not self.request.user.groups.filter(name="Analyst").exists()
        ):
            qs = qs.filter(
                pk__in=DistributionAssignment.objects.filter(
                    publisher__user=self.request.user
                )
                .exclude(status="revoked")
                .values("candidate_id")
            )
        for key in ("review_status", "language", "category"):
            if self.request.query_params.get(key):
                qs = qs.filter(**{key: self.request.query_params[key]})
        if self.request.query_params.get("q"):
            qs = qs.filter(title__icontains=self.request.query_params["q"])
        return qs.order_by("-score", "-pk")

    @action(detail=True, methods=["post"], permission_classes=[StaffOnly])
    def review(self, request, pk=None):
        s = ReviewInput(data=request.data)
        s.is_valid(raise_exception=True)
        candidate = operation(
            lambda: review(self.get_object(), request.user, **s.validated_data)
        )
        return Response(CandidateSerializer(candidate).data)

    @action(detail=True, methods=["post"], permission_classes=[StaffOnly])
    def assign(self, request, pk=None):
        s = AssignInput(data=request.data)
        s.is_valid(raise_exception=True)
        candidate = self.get_object()
        from django.db import transaction

        with transaction.atomic():
            result = [
                operation(lambda p=p: assign(candidate, p, request.user))[0]
                for p in s.validated_data["publishers"]
            ]
        return Response(AssignmentSerializer(result, many=True).data, status=201)

    @action(
        detail=False,
        methods=["post"],
        permission_classes=[StaffOnly],
        url_path="import",
    )
    def import_candidates(self, request):
        s = CandidateRecordSerializer(data=request.data, many=True)
        s.is_valid(raise_exception=True)
        if len(request.data) > 1000:
            raise serializers.ValidationError("At most 1000 records per import.")
        provider, _ = DiscoveryProvider.objects.get_or_create(
            name="Manual authorized import", defaults={"kind": "manual"}
        )
        run = DiscoveryRun.objects.create(provider=provider)
        try:
            count = operation(lambda: ingest(provider, run, request.data))
        except Exception:
            run.status = "failed"
            run.finished_at = timezone.now()
            run.error = "Import validation failed."
            run.save()
            raise
        run.status = "success"
        run.candidates_seen = count
        run.finished_at = timezone.now()
        run.save()
        audit(request.user, "import", run, {"count": count})
        return Response({"run": run.pk, "count": count}, status=201)


class ReviewInput(serializers.Serializer):
    decision = serializers.ChoiceField(choices=["approved", "rejected"])
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    rights = serializers.ChoiceField(
        choices=["unknown", "owned", "licensed", "permission"], required=False
    )
    evidence = serializers.CharField(required=False, allow_blank=True)


class AssignInput(serializers.Serializer):
    publishers = serializers.PrimaryKeyRelatedField(
        queryset=PublisherProfile.objects.filter(active=True),
        many=True,
        allow_empty=False,
    )


class TransitionInput(serializers.Serializer):
    status = serializers.ChoiceField(choices=["accepted", "declined", "revoked"])


class PublishInput(serializers.Serializer):
    url = serializers.URLField(max_length=1000)
    published_at = serializers.DateTimeField(default=timezone.now)

    def validate_url(self, value):
        return operation(lambda: safe_url(value))


class AssignmentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AssignmentSerializer

    def get_queryset(self):
        qs = DistributionAssignment.objects.select_related("candidate", "publisher")
        if not self.request.user.is_staff:
            qs = qs.filter(publisher__user=self.request.user)
        return qs.order_by("-pk")

    @action(detail=True, methods=["post"])
    def transition(self, request, pk=None):
        s = TransitionInput(data=request.data)
        s.is_valid(raise_exception=True)
        a = operation(
            lambda: transition(
                self.get_object(), request.user, s.validated_data["status"]
            )
        )
        return Response(AssignmentSerializer(a).data)

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        s = PublishInput(data=request.data)
        s.is_valid(raise_exception=True)
        p = operation(
            lambda: publish(self.get_object(), request.user, **s.validated_data)
        )
        return Response(PostSerializer(p).data, status=201)


class PostViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PostSerializer

    def get_queryset(self):
        qs = PublishedPost.objects.all()
        if not self.request.user.is_staff:
            qs = qs.filter(assignment__publisher__user=self.request.user)
        return qs.order_by("-pk")


class MetricViewSet(viewsets.ModelViewSet):
    serializer_class = MetricSerializer
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        qs = PerformanceSnapshot.objects.all()
        if not self.request.user.is_staff:
            qs = qs.filter(post__assignment__publisher__user=self.request.user)
        return qs.order_by("-observed_at")

    def perform_create(self, serializer):
        post = serializer.validated_data["post"]
        if (
            not self.request.user.is_staff
            and post.assignment.publisher.user_id != self.request.user.pk
        ):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied()
        metric = serializer.save(entered_by=self.request.user)
        audit(self.request.user, "metric_report", metric)

    @action(detail=True, methods=["post"], permission_classes=[StaffOnly])
    def verify(self, request, pk=None):
        metric = self.get_object()
        metric.verified = True
        metric.save(update_fields=["verified"])
        audit(request.user, "metric_verified", metric)
        return Response(self.get_serializer(metric).data)
