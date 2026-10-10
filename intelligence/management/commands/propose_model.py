from collections import defaultdict
from statistics import mean
from django.core.management.base import BaseCommand, CommandError
from intelligence.models import PerformanceSnapshot, RankingModelVersion, ViralScore
from intelligence.ranking import DEFAULT_WEIGHTS, DEFAULT_BENCHMARKS


class Command(BaseCommand):
    help = "Generate an inactive, auditable weight proposal from at least 30 distinct verified publications."

    def add_arguments(self, parser):
        parser.add_argument("--model-version", required=True)

    def handle(self, *args, **options):
        posts = {}
        for metric in (
            PerformanceSnapshot.objects.filter(verified=True, views__isnull=False)
            .select_related("post__assignment__candidate")
            .order_by("observed_at")
        ):
            hours = (
                metric.observed_at - metric.post.published_at
            ).total_seconds() / 3600
            if 12 <= hours <= 36:
                posts[metric.post_id] = metric
        if len(posts) < 30:
            raise CommandError(
                "At least 30 distinct verified outcomes at 12–36 hours are required."
            )
        values = defaultdict(list)
        for metric in posts.values():
            assignment = metric.post.assignment
            history = (
                ViralScore.objects.filter(
                    candidate=assignment.candidate,
                    created_at__lte=assignment.created_at,
                )
                .order_by("-created_at")
                .first()
            )
            if not history:
                continue
            for key, signal in history.components.items():
                values[key].append((signal, metric.views))
        import math

        correlations = {}
        for key, pairs in values.items():
            if len(pairs) < 20:
                continue
            xs = [p[0] for p in pairs]
            ys = [math.log1p(p[1]) for p in pairs]
            xm, ym = mean(xs), mean(ys)
            denominator = math.sqrt(
                sum((x - xm) ** 2 for x in xs) * sum((y - ym) ** 2 for y in ys)
            )
            if denominator:
                correlations[key] = (
                    sum((x - xm) * (y - ym) for x, y in zip(xs, ys)) / denominator
                )
        if not correlations:
            raise CommandError(
                "Insufficient varied pre-assignment evidence to propose changes."
            )
        weights = {
            k: v * (1 + max(-0.2, min(0.2, correlations.get(k, 0))))
            for k, v in DEFAULT_WEIGHTS.items()
        }
        total = sum(weights.values())
        weights = {k: round(100 * v / total, 3) for k, v in weights.items()}
        _, created = RankingModelVersion.objects.get_or_create(
            version=options["model_version"],
            defaults={
                "weights": weights,
                "benchmarks": DEFAULT_BENCHMARKS,
                "active": False,
                "evidence": {
                    "verified_posts": len(posts),
                    "correlations": correlations,
                    "status": "Review required; in-sample association is not predictive validation",
                    "method": "Bounded +/-20% adjustment using pre-assignment signals and 12–36h log views",
                },
            },
        )
        if not created:
            raise CommandError("Version already exists; choose a new identifier.")
        self.stdout.write(
            "Inactive proposal saved. Validate on held-out outcomes before activation."
        )
