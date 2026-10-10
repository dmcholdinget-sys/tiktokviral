import json, secrets
from collections import Counter
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import IntegrityError, transaction
from django.db.models import Count, Sum
from django.http import JsonResponse, FileResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import *
from .forms import *
from .services import review, assign, transition, publish, audit, can_use_media
from .api import MetricSerializer
from .providers import run_discovery
from .telegram import bot_request

staff_required = user_passes_test(lambda u: u.is_authenticated and u.is_staff)


reader_required = user_passes_test(
    lambda u: (
        u.is_authenticated and (u.is_staff or u.groups.filter(name="Analyst").exists())
    )
)


def candidate_scope(user):
    qs = VideoCandidate.objects.all()
    if user.is_staff or user.groups.filter(name="Analyst").exists():
        return qs
    return qs.filter(
        pk__in=DistributionAssignment.objects.filter(publisher__user=user)
        .exclude(status="revoked")
        .values("candidate_id")
    )


def assignment_scope(user):
    qs = DistributionAssignment.objects.select_related("candidate", "publisher")
    return qs if user.is_staff else qs.filter(publisher__user=user)


@login_required
def dashboard(request):
    qs = candidate_scope(request.user)
    if (
        not request.user.is_staff
        and not request.user.groups.filter(name="Analyst").exists()
    ):
        return redirect("assignments")
    context = {
        "candidate_count": qs.count(),
        "approved_count": qs.filter(review_status="approved").count(),
        "pending_count": qs.filter(review_status="pending").count(),
        "published_count": PublishedPost.objects.count(),
        "candidates": qs.order_by("-score", "-pk")[:10],
        "runs": DiscoveryRun.objects.select_related("provider").order_by("-pk")[:5],
        "deliveries": TelegramDelivery.objects.values("status").annotate(
            count=Count("id")
        ),
        "live_provider": DiscoveryProvider.objects.filter(
            kind__in=["feed", "browser"], enabled=True
        ).exists(),
    }
    return render(request, "intelligence/dashboard.html", context)


@login_required
def candidates(request):
    qs = candidate_scope(request.user)
    for key in ("review_status", "language", "category"):
        if request.GET.get(key):
            qs = qs.filter(**{key: request.GET[key]})
    if request.GET.get("q"):
        qs = qs.filter(title__icontains=request.GET["q"])
    from django.core.paginator import Paginator

    return render(
        request,
        "intelligence/candidates.html",
        {
            "page": Paginator(qs.order_by("-score", "-pk"), 30).get_page(
                request.GET.get("page")
            )
        },
    )


@login_required
def candidate_detail(request, pk):
    candidate = get_object_or_404(candidate_scope(request.user), pk=pk)
    rf = ReviewForm(
        initial={"rights": candidate.rights, "evidence": candidate.rights_evidence}
    )
    af = AssignForm()
    if request.method == "POST":
        if not request.user.is_staff:
            raise PermissionDenied
        try:
            if request.POST.get("action") == "review":
                rf = ReviewForm(request.POST)
                if rf.is_valid():
                    candidate = review(candidate, request.user, **rf.cleaned_data)
                    messages.success(request, "Review saved.")
                    return redirect("candidate-detail", pk=pk)
            elif request.POST.get("action") == "assign":
                af = AssignForm(request.POST)
                if af.is_valid():
                    with transaction.atomic():
                        for publisher in af.cleaned_data["publishers"]:
                            assign(candidate, publisher, request.user)
                    messages.success(
                        request,
                        "Assignments queued. Telegram requires a linked chat and configured bot.",
                    )
                    return redirect("candidate-detail", pk=pk)
        except ValidationError as exc:
            messages.error(request, " ".join(exc.messages))
    return render(
        request,
        "intelligence/detail.html",
        {
            "candidate": candidate,
            "review_form": rf,
            "assign_form": af,
            "media_allowed": can_use_media(candidate),
        },
    )


@login_required
def assignments(request):
    return render(
        request,
        "intelligence/assignments.html",
        {"assignments": assignment_scope(request.user).order_by("-pk")[:100]},
    )


@login_required
def assignment_detail(request, pk):
    assignment = get_object_or_404(assignment_scope(request.user), pk=pk)
    pf = PublicationForm(initial={"published_at": timezone.localtime()})
    mf = PerformanceForm(initial={"observed_at": timezone.localtime()})
    if request.method == "POST":
        try:
            action = request.POST.get("action")
            if action in ("accepted", "declined", "revoked"):
                transition(assignment, request.user, action)
            elif action == "publish":
                pf = PublicationForm(request.POST)
                if not pf.is_valid():
                    return render(
                        request,
                        "intelligence/assignment.html",
                        {
                            "assignment": assignment,
                            "publication_form": pf,
                            "metric_form": mf,
                        },
                    )
                publish(assignment, request.user, **pf.cleaned_data)
            elif action == "metric":
                mf = PerformanceForm(request.POST)
                if mf.is_valid():
                    post = get_object_or_404(PublishedPost, assignment=assignment)
                    if (
                        not request.user.is_staff
                        and assignment.publisher.user_id != request.user.pk
                    ):
                        raise PermissionDenied
                    data = {k: v for k, v in mf.cleaned_data.items() if v is not None}
                    data["post"] = post.pk
                    s = MetricSerializer(data=data)
                    if s.is_valid():
                        metric = s.save(entered_by=request.user)
                        audit(request.user, "metric_report", metric)
                    else:
                        messages.error(request, str(s.errors))
                else:
                    return render(
                        request,
                        "intelligence/assignment.html",
                        {
                            "assignment": assignment,
                            "publication_form": pf,
                            "metric_form": mf,
                        },
                    )
            messages.success(request, "Update saved.")
            return redirect("assignment-detail", pk=pk)
        except (ValidationError, IntegrityError) as exc:
            messages.error(
                request,
                " ".join(exc.messages)
                if isinstance(exc, ValidationError)
                else "Duplicate publication URL.",
            )
    return render(
        request,
        "intelligence/assignment.html",
        {"assignment": assignment, "publication_form": pf, "metric_form": mf},
    )


@login_required
def trends(request):
    topics = Counter()
    for candidate in candidate_scope(request.user):
        for topic in set(
            candidate.signals.get("topics", []) + candidate.signals.get("hashtags", [])
        ):
            topics[topic] += 1
    return render(
        request,
        "intelligence/trends.html",
        {
            "topics": topics.most_common(50),
            "clusters": TrendCluster.objects.filter(
                candidates__in=candidate_scope(request.user)
            ).distinct(),
        },
    )


@reader_required
def reports(request):
    publishers = PublisherProfile.objects.annotate(
        assigned=Count("assignments", distinct=True),
        published=Count("assignments__publication", distinct=True),
    )
    summary = {}
    for publisher in publishers:
        views = []
        followers = []
        for post in PublishedPost.objects.filter(assignment__publisher=publisher):
            metric = post.metrics.order_by("-observed_at").first()
            if metric:
                if metric.views is not None:
                    views.append(metric.views)
                if metric.followers_gained is not None:
                    followers.append(metric.followers_gained)
        summary[publisher.pk] = {
            "views": sum(views) if views else None,
            "followers": sum(followers) if followers else None,
        }
        publisher.reported_views = summary[publisher.pk]["views"]
        publisher.reported_followers = summary[publisher.pk]["followers"]
    return render(
        request,
        "intelligence/reports.html",
        {
            "publishers": publishers,
            "verified_count": PerformanceSnapshot.objects.filter(verified=True).count(),
            "self_count": PerformanceSnapshot.objects.filter(verified=False).count(),
            "models": RankingModelVersion.objects.order_by("-created_at"),
            "recent_metrics": PerformanceSnapshot.objects.select_related(
                "post__assignment__publisher"
            ).order_by("-observed_at")[:30],
        },
    )


@staff_required
def integrations(request):
    return render(
        request,
        "intelligence/integrations.html",
        {
            "providers": DiscoveryProvider.objects.all(),
            "runs": DiscoveryRun.objects.select_related("provider").order_by("-pk")[
                :30
            ],
            "bot_configured": bool(settings.TELEGRAM_BOT_TOKEN),
            "feed_configured": bool(settings.DISCOVERY_FEED_URL),
            "publishers": PublisherProfile.objects.select_related("user").all(),
        },
    )


@staff_required
@require_POST
def discover(request, pk):
    provider = get_object_or_404(DiscoveryProvider, pk=pk)
    run = run_discovery(provider)
    audit(request.user, "discovery_requested", run)
    if run.status == "success":
        messages.success(request, f"Ingested {run.candidates_seen} records.")
    else:
        messages.error(request, run.error)
    return redirect("integrations")


@staff_required
@require_POST
def verify_metric(request, pk):
    metric = get_object_or_404(PerformanceSnapshot, pk=pk)
    metric.verified = True
    metric.save(update_fields=["verified"])
    audit(request.user, "metric_verified", metric)
    return redirect("reports")


@login_required
def private_media(request, pk):
    media = get_object_or_404(MediaAsset.objects.select_related("candidate"), pk=pk)
    if not candidate_scope(request.user).filter(pk=media.candidate_id).exists():
        raise PermissionDenied
    if not can_use_media(media.candidate):
        raise PermissionDenied("Current documented media rights are required.")
    audit(request.user, "media_download", media)
    return FileResponse(media.file.open("rb"), as_attachment=True)


@csrf_exempt
@require_POST
def telegram_webhook(request):
    expected = settings.TELEGRAM_WEBHOOK_SECRET
    if not expected or not secrets.compare_digest(
        request.headers.get("X-Telegram-Bot-Api-Secret-Token", ""), expected
    ):
        return JsonResponse({"error": "Forbidden"}, status=403)
    if len(request.body) > 100000:
        return JsonResponse({"error": "Too large"}, status=413)
    try:
        data = json.loads(request.body)
    except ValueError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    if not isinstance(data, dict):
        return JsonResponse({"error": "Expected an object"}, status=400)
    message = data.get("message", {})
    if message.get("chat", {}).get("type") == "private" and message.get(
        "text", ""
    ).startswith("/start "):
        token = message["text"].split(" ", 1)[1].strip()
        try:
            with transaction.atomic():
                profile = PublisherProfile.objects.select_for_update().get(
                    link_token=token, active=True
                )
                if profile.telegram_chat_id:
                    return JsonResponse({"ok": True})
                profile.telegram_chat_id = str(message["chat"]["id"])
                import uuid

                profile.link_token = uuid.uuid4()
                profile.save()
                audit(profile.user, "telegram_linked", profile)
        except (
            PublisherProfile.DoesNotExist,
            ValidationError,
            ValueError,
            IntegrityError,
        ):
            return JsonResponse({"ok": True})
    if message.get("chat", {}).get("type") == "private" and message.get(
        "text", ""
    ).startswith("/published "):
        parts = message["text"].split()
        if len(parts) == 3 and parts[1].isdigit():
            profile = PublisherProfile.objects.filter(
                telegram_chat_id=str(message["chat"]["id"]),
                active=True,
                user__is_active=True,
            ).first()
            if profile:
                assignment = DistributionAssignment.objects.filter(
                    pk=parts[1], publisher=profile
                ).first()
                if assignment:
                    try:
                        publish(assignment, profile.user, parts[2], timezone.now())
                    except (ValidationError, IntegrityError):
                        pass
    callback = data.get("callback_query", {})
    if callback:
        chat = callback.get("message", {}).get("chat", {})
        parts = callback.get("data", "").split(":")
        if (
            chat.get("type") == "private"
            and len(parts) == 2
            and parts[0] in ("accept", "decline")
            and parts[1].isdigit()
        ):
            profile = PublisherProfile.objects.filter(
                telegram_chat_id=str(chat.get("id")), active=True, user__is_active=True
            ).first()
            if (
                profile
                and str(callback.get("from", {}).get("id")) == profile.telegram_chat_id
            ):
                assignment = DistributionAssignment.objects.filter(
                    pk=parts[1], publisher=profile
                ).first()
                if assignment:
                    try:
                        transition(
                            assignment,
                            profile.user,
                            {"accept": "accepted", "decline": "declined"}[parts[0]],
                        )
                    except ValidationError:
                        pass
        try:
            bot_request(
                "answerCallbackQuery",
                {
                    "callback_query_id": callback["id"],
                    "text": "Recorded if this assignment is available to you.",
                },
            )
        except Exception:
            pass
    return JsonResponse({"ok": True})


@staff_required
@require_POST
def reconcile(request, pk):
    from .services import reconcile_delivery

    delivery = get_object_or_404(TelegramDelivery, pk=pk)
    try:
        reconcile_delivery(
            delivery,
            request.user,
            request.POST.get("resolution"),
            request.POST.get("note", ""),
        )
        messages.success(request, "Delivery reconciliation saved.")
    except ValidationError as exc:
        messages.error(request, " ".join(exc.messages))
    return redirect("assignment-detail", pk=delivery.assignment_id)


@login_required
@require_POST
def notification_read(request, pk):
    note = get_object_or_404(Notification, pk=pk, user=request.user)
    note.read = True
    note.save(update_fields=["read"])
    return redirect(note.path)


@reader_required
def export_report(request):
    import csv
    from django.http import HttpResponse

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="publishing-outcomes.csv"'
    writer = csv.writer(response)
    writer.writerow(
        [
            "assignment",
            "publisher",
            "candidate_id",
            "publication_url",
            "published_at",
            "observed_at",
            "views",
            "likes",
            "comments",
            "shares",
            "followers_gained",
            "verified",
        ]
    )

    def cell(value):
        value = "" if value is None else str(value)
        return "'" + value if value.startswith(("=", "+", "-", "@")) else value

    for metric in (
        PerformanceSnapshot.objects.select_related(
            "post__assignment__publisher", "post__assignment__candidate"
        )
        .order_by("pk")
        .iterator()
    ):
        a = metric.post.assignment
        writer.writerow(
            [
                cell(x)
                for x in [
                    a.pk,
                    a.publisher.display_name,
                    a.candidate.canonical_id,
                    metric.post.url,
                    metric.post.published_at,
                    metric.observed_at,
                    metric.views,
                    metric.likes,
                    metric.comments,
                    metric.shares,
                    metric.followers_gained,
                    metric.verified,
                ]
            ]
        )
    audit(request.user, "report_export", request.user)
    return response
