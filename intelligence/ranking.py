from django.utils import timezone
from .models import RankingModelVersion, ViralScore

DEFAULT_WEIGHTS = {
    "velocity": 25,
    "acceleration": 20,
    "engagement": 15,
    "relevance": 15,
    "freshness": 10,
    "propagation": 10,
    "novelty": 5,
}
DEFAULT_BENCHMARKS = {
    "views_per_hour": 10000,
    "acceleration_per_hour": 10000,
    "engagement_rate": 0.12,
    "min_completeness": 0.35,
}


def clamp(value):
    return max(0.0, min(1.0, float(value)))


def score_candidate(candidate):
    model = (
        RankingModelVersion.objects.filter(active=True).order_by("-created_at").first()
    )
    weights = model.weights if model else DEFAULT_WEIGHTS
    benchmarks = {**DEFAULT_BENCHMARKS, **(model.benchmarks if model else {})}
    snapshots = list(candidate.snapshots.order_by("observed_at"))
    now = timezone.now()
    components = {}
    usable = [s for s in snapshots if s.views is not None]
    velocities = []
    for before, after in zip(usable, usable[1:]):
        hours = (after.observed_at - before.observed_at).total_seconds() / 3600
        if hours > 0 and after.views >= before.views:
            velocities.append((after.observed_at, (after.views - before.views) / hours))
    if velocities:
        components["velocity"] = clamp(velocities[-1][1] / benchmarks["views_per_hour"])
    if len(velocities) >= 2:
        hours = (velocities[-1][0] - velocities[-2][0]).total_seconds() / 3600
        if hours > 0:
            components["acceleration"] = clamp(
                (velocities[-1][1] - velocities[-2][1])
                / hours
                / benchmarks["acceleration_per_hour"]
            )
    latest = snapshots[-1] if snapshots else None
    if (
        latest
        and latest.views
        and all(getattr(latest, k) is not None for k in ("likes", "comments", "shares"))
    ):
        components["engagement"] = clamp(
            (latest.likes + latest.comments + latest.shares)
            / latest.views
            / benchmarks["engagement_rate"]
        )
    for key in ("relevance", "propagation", "novelty"):
        if candidate.signals.get(key) is not None:
            components[key] = clamp(candidate.signals[key])
    if candidate.published_at:
        age = max(0, (now - candidate.published_at).total_seconds() / 3600)
        components["freshness"] = clamp(1 - age / 24)
    total = sum(weights.values())
    available = sum(weights.get(k, 0) for k in components)
    completeness = available / total if total else 0
    eligible = completeness >= benchmarks["min_completeness"] and any(
        k in components for k in ("velocity", "engagement")
    )
    value = (
        round(
            100
            * sum(components[k] * weights.get(k, 0) for k in components)
            / available,
            2,
        )
        if eligible and available
        else None
    )
    stale = not latest or (now - latest.observed_at).total_seconds() > 3600
    confidence = (
        ("High" if completeness >= 0.8 else "Medium" if completeness >= 0.55 else "Low")
        if value is not None
        else "Insufficient Data"
    )
    if stale and value is not None:
        confidence = "Low"
    candidate.score = value
    candidate.completeness = round(completeness, 3)
    candidate.confidence = confidence
    candidate.score_components = components
    candidate.algorithm_version = model.version if model else "baseline-v1"
    candidate.save(
        update_fields=[
            "score",
            "completeness",
            "confidence",
            "score_components",
            "algorithm_version",
        ]
    )
    ViralScore.objects.create(
        candidate=candidate,
        value=value,
        completeness=completeness,
        components=components,
        version=candidate.algorithm_version,
    )
    return candidate
