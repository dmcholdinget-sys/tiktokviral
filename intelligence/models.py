import uuid
from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class PublisherProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    display_name = models.CharField(max_length=120)
    telegram_chat_id = models.CharField(
        max_length=64, blank=True, unique=True, null=True
    )
    link_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    active = models.BooleanField(default=True)
    daily_limit = models.PositiveIntegerField(default=5)

    def __str__(self):
        return self.display_name


class DiscoveryProvider(models.Model):
    name = models.CharField(max_length=120, unique=True)
    kind = models.CharField(
        max_length=20,
        choices=[
            ("fixture", "Fixture / demo"),
            ("feed", "Authorized JSON feed"),
            ("manual", "Manual import"),
            ("browser", "Playwright public-page discovery"),
        ],
    )
    enabled = models.BooleanField(default=False)
    capabilities = models.JSONField(default=dict, blank=True)
    last_success = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name


class DiscoveryRun(models.Model):
    provider = models.ForeignKey(DiscoveryProvider, on_delete=models.PROTECT)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, default="running")
    candidates_seen = models.PositiveIntegerField(default=0)
    error = models.TextField(blank=True)


class RankingModelVersion(models.Model):
    version = models.CharField(max_length=64, unique=True)
    weights = models.JSONField(default=dict)
    benchmarks = models.JSONField(default=dict)
    active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    evidence = models.JSONField(default=dict, blank=True)

    def clean(self):
        from django.core.exceptions import ValidationError
        import math

        keys = {
            "velocity",
            "acceleration",
            "engagement",
            "relevance",
            "freshness",
            "propagation",
            "novelty",
        }
        if (
            set(self.weights) != keys
            or any(
                not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0
                for v in self.weights.values()
            )
            or sum(self.weights.values()) <= 0
        ):
            raise ValidationError(
                "Supply nonnegative finite weights for all seven components, with a positive total."
            )
        for key in ("views_per_hour", "acceleration_per_hour", "engagement_rate"):
            value = self.benchmarks.get(key, 1)
            if (
                not isinstance(value, (int, float))
                or not math.isfinite(value)
                or value <= 0
            ):
                raise ValidationError("Benchmarks must be positive finite numbers.")
        if not 0 <= self.benchmarks.get("min_completeness", 0.35) <= 1:
            raise ValidationError("Completeness must be between 0 and 1.")
        if (
            self.active
            and RankingModelVersion.objects.filter(active=True)
            .exclude(pk=self.pk)
            .exists()
        ):
            raise ValidationError(
                "Deactivate the existing model before activating another."
            )

    def __str__(self):
        return self.version


class VideoCandidate(models.Model):
    platform = models.CharField(max_length=32, default="tiktok")
    canonical_id = models.CharField(max_length=160)
    url = models.URLField(max_length=1000)
    title = models.CharField(max_length=500)
    creator = models.CharField(max_length=120, blank=True)
    language = models.CharField(max_length=32, blank=True)
    category = models.CharField(max_length=64, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    discovered_at = models.DateTimeField(auto_now_add=True)
    signals = models.JSONField(default=dict, blank=True)
    review_status = models.CharField(
        max_length=20,
        default="pending",
        choices=[
            ("pending", "Pending"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
            ("expired", "Expired"),
        ],
    )
    rights = models.CharField(
        max_length=24,
        default="unknown",
        choices=[
            ("unknown", "Unknown / link only"),
            ("owned", "Owned"),
            ("licensed", "Licensed"),
            ("permission", "Permission granted"),
        ],
    )
    rights_evidence = models.TextField(blank=True)
    rights_expires_at = models.DateTimeField(null=True, blank=True)
    safety_flags = models.JSONField(default=list, blank=True)
    score = models.FloatField(null=True, blank=True)
    completeness = models.FloatField(default=0)
    confidence = models.CharField(max_length=32, default="Insufficient Data")
    score_components = models.JSONField(default=dict, blank=True)
    algorithm_version = models.CharField(max_length=64, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["platform", "canonical_id"], name="canonical_candidate_unique"
            )
        ]
        ordering = ["-score", "-discovered_at"]

    def __str__(self):
        return self.title

    @property
    def score_label(self):
        if self.score is None:
            return "Insufficient Data"
        for threshold, label in [
            (85, "Breakout Candidate"),
            (70, "Rising Fast"),
            (55, "Worth Watching"),
            (40, "Early / Uncertain"),
        ]:
            if self.score >= threshold:
                return label
        return "Low Priority"


class CandidateDiscovery(models.Model):
    candidate = models.ForeignKey(
        VideoCandidate, on_delete=models.CASCADE, related_name="provenance"
    )
    run = models.ForeignKey(DiscoveryRun, on_delete=models.PROTECT)
    source_timestamp = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["candidate", "run"], name="candidate_run_unique"
            )
        ]


class EngagementSnapshot(models.Model):
    candidate = models.ForeignKey(
        VideoCandidate, on_delete=models.CASCADE, related_name="snapshots"
    )
    provider = models.ForeignKey(DiscoveryProvider, on_delete=models.PROTECT)
    observed_at = models.DateTimeField()
    collected_at = models.DateTimeField(auto_now_add=True)
    views = models.PositiveBigIntegerField(null=True, blank=True)
    likes = models.PositiveBigIntegerField(null=True, blank=True)
    comments = models.PositiveBigIntegerField(null=True, blank=True)
    shares = models.PositiveBigIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["observed_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["candidate", "provider", "observed_at"],
                name="snapshot_source_time_unique",
            )
        ]


class ViralScore(models.Model):
    candidate = models.ForeignKey(
        VideoCandidate, on_delete=models.CASCADE, related_name="score_history"
    )
    value = models.FloatField(null=True)
    completeness = models.FloatField()
    components = models.JSONField(default=dict)
    version = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)


class ContentReview(models.Model):
    candidate = models.ForeignKey(
        VideoCandidate, on_delete=models.CASCADE, related_name="reviews"
    )
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    decision = models.CharField(max_length=20)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class MediaAsset(models.Model):
    candidate = models.ForeignKey(
        VideoCandidate, on_delete=models.CASCADE, related_name="media_assets"
    )
    file = models.FileField(upload_to="private/%Y/%m/")
    description = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class DistributionAssignment(models.Model):
    candidate = models.ForeignKey(
        VideoCandidate, on_delete=models.PROTECT, related_name="assignments"
    )
    publisher = models.ForeignKey(
        PublisherProfile, on_delete=models.PROTECT, related_name="assignments"
    )
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    status = models.CharField(
        max_length=24,
        default="queued",
        choices=[
            (s, s.title())
            for s in ["queued", "sent", "accepted", "declined", "published", "revoked"]
        ],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["candidate", "publisher"], name="assignment_unique"
            )
        ]


class TelegramDelivery(models.Model):
    assignment = models.OneToOneField(
        DistributionAssignment, on_delete=models.CASCADE, related_name="delivery"
    )
    status = models.CharField(max_length=24, default="pending")
    attempts = models.PositiveIntegerField(default=0)
    next_attempt_at = models.DateTimeField(null=True, blank=True)
    message_id = models.CharField(max_length=64, blank=True)
    error = models.TextField(blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)


class PublishedPost(models.Model):
    assignment = models.OneToOneField(
        DistributionAssignment, on_delete=models.PROTECT, related_name="publication"
    )
    url = models.URLField(max_length=1000, unique=True)
    published_at = models.DateTimeField()
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class PerformanceSnapshot(models.Model):
    post = models.ForeignKey(
        PublishedPost, on_delete=models.CASCADE, related_name="metrics"
    )
    observed_at = models.DateTimeField()
    views = models.PositiveBigIntegerField(null=True, blank=True)
    likes = models.PositiveBigIntegerField(null=True, blank=True)
    comments = models.PositiveBigIntegerField(null=True, blank=True)
    shares = models.PositiveBigIntegerField(null=True, blank=True)
    followers_gained = models.PositiveIntegerField(null=True, blank=True)
    verified = models.BooleanField(default=False)
    source = models.CharField(max_length=32, default="self_reported")
    entered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)


class AuditLog(models.Model):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL
    )
    action = models.CharField(max_length=64)
    object_type = models.CharField(max_length=64)
    object_id = models.CharField(max_length=64)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class TrendSignal(models.Model):
    kind = models.CharField(
        max_length=24,
        choices=[("topic", "Topic"), ("hashtag", "Hashtag"), ("sound", "Sound")],
    )
    value = models.CharField(max_length=120)
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    candidates = models.ManyToManyField(VideoCandidate, related_name="trend_signals")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["kind", "value"], name="trend_signal_unique"
            )
        ]


class TrendCluster(models.Model):
    name = models.CharField(max_length=120, unique=True)
    candidates = models.ManyToManyField(VideoCandidate, related_name="clusters")
    lifecycle = models.CharField(
        max_length=24,
        default="emerging",
        choices=[
            (v, v.title())
            for v in ["emerging", "rising", "peak", "saturated", "declining"]
        ],
    )
    updated_at = models.DateTimeField(auto_now=True)


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    key = models.CharField(max_length=160, unique=True)
    message = models.CharField(max_length=500)
    path = models.CharField(max_length=200, default="/")
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
