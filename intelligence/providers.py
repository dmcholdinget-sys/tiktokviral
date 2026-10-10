"""Authorized, replaceable data providers. No TikTok scraping or account automation."""

from datetime import timedelta
import requests
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from .models import *
from .ranking import score_candidate
from .services import safe_url


class ObservationSerializer(serializers.Serializer):
    observed_at = serializers.DateTimeField()
    views = serializers.IntegerField(min_value=0, allow_null=True, required=False)
    likes = serializers.IntegerField(min_value=0, allow_null=True, required=False)
    comments = serializers.IntegerField(min_value=0, allow_null=True, required=False)
    shares = serializers.IntegerField(min_value=0, allow_null=True, required=False)

    def validate_observed_at(self, value):
        if value > timezone.now() + timedelta(minutes=5):
            raise serializers.ValidationError("Observation is in the future.")
        return value


class CandidateRecordSerializer(serializers.Serializer):
    platform = serializers.ChoiceField(
        choices=["tiktok", "youtube", "instagram", "fixture"], default="tiktok"
    )
    canonical_id = serializers.CharField(max_length=160)
    url = serializers.URLField(max_length=1000)
    title = serializers.CharField(max_length=500)
    creator = serializers.CharField(max_length=120, required=False, allow_blank=True)
    language = serializers.CharField(max_length=32, required=False, allow_blank=True)
    category = serializers.CharField(max_length=64, required=False, allow_blank=True)
    published_at = serializers.DateTimeField(required=False, allow_null=True)
    source_timestamp = serializers.DateTimeField(required=False, allow_null=True)
    signals = serializers.DictField(required=False, default=dict)
    safety_flags = serializers.ListField(
        child=serializers.CharField(max_length=120), required=False, default=list
    )
    observations = ObservationSerializer(many=True, required=False, default=list)

    def validate_url(self, value):
        from django.core.exceptions import ValidationError

        try:
            return safe_url(value)
        except ValidationError as exc:
            raise serializers.ValidationError(exc.messages)

    def validate_published_at(self, value):
        if value and value > timezone.now() + timedelta(minutes=5):
            raise serializers.ValidationError("Publication is in the future.")
        return value

    def validate_signals(self, value):
        for key in ("relevance", "propagation", "novelty"):
            if key in value and value[key] is not None:
                if (
                    isinstance(value[key], bool)
                    or not isinstance(value[key], (int, float))
                    or not 0 <= value[key] <= 1
                ):
                    raise serializers.ValidationError(f"{key} must be between 0 and 1.")
        for key in ("hashtags", "sounds", "topics"):
            if key in value and (
                not isinstance(value[key], list)
                or len(value[key]) > 100
                or any(not isinstance(x, str) or len(x) > 120 for x in value[key])
            ):
                raise serializers.ValidationError(
                    f"{key} must be a list of short strings."
                )
        return value


class FixtureProvider:
    def discover(self):
        now = timezone.now()
        return [
            {
                "platform": "fixture",
                "canonical_id": "ethiopian-demo-1",
                "url": "https://example.com/demo-opportunity",
                "title": "DEMO · Ethiopian coffee ceremony storytelling",
                "creator": "Fixture creator",
                "language": "am",
                "category": "Culture",
                "published_at": (now - timedelta(hours=3)).isoformat(),
                "source_timestamp": now.isoformat(),
                "signals": {
                    "relevance": 0.95,
                    "propagation": 0.7,
                    "novelty": 0.8,
                    "hashtags": ["ethiopia", "ቡና"],
                    "topics": ["Coffee culture"],
                    "sounds": ["Original narration"],
                },
                "observations": [
                    {
                        "observed_at": (now - timedelta(hours=2)).isoformat(),
                        "views": 1000,
                        "likes": 100,
                        "comments": 15,
                        "shares": 20,
                    },
                    {
                        "observed_at": (now - timedelta(hours=1)).isoformat(),
                        "views": 4000,
                        "likes": 400,
                        "comments": 60,
                        "shares": 80,
                    },
                    {
                        "observed_at": now.isoformat(),
                        "views": 16000,
                        "likes": 1600,
                        "comments": 240,
                        "shares": 320,
                    },
                ],
            }
        ]


class AuthorizedFeedProvider:
    def discover(self):
        if not settings.DISCOVERY_FEED_URL:
            raise ValueError("Configure DISCOVERY_FEED_URL for an approved source.")
        safe_url(settings.DISCOVERY_FEED_URL)
        headers = (
            {"Authorization": f"Bearer {settings.DISCOVERY_API_TOKEN}"}
            if settings.DISCOVERY_API_TOKEN
            else {}
        )
        response = requests.get(
            settings.DISCOVERY_FEED_URL,
            headers=headers,
            timeout=30,
            allow_redirects=False,
            stream=True,
        )
        response.raise_for_status()
        if response.status_code != 200:
            raise ValueError("Feed must return HTTP 200 without redirects.")
        raw = bytearray()
        for chunk in response.iter_content(65536):
            raw.extend(chunk)
            if len(raw) > 5_000_000:
                raise ValueError("Feed exceeds 5 MB limit.")
        import json

        data = json.loads(raw)
        if not isinstance(data, list) or len(data) > 1000:
            raise ValueError("Feed must be a list of at most 1000 candidates.")
        return data


@transaction.atomic
def ingest(provider, run, records):
    serializer = CandidateRecordSerializer(data=records, many=True)
    serializer.is_valid(raise_exception=True)
    for record in serializer.validated_data:
        observations = record.pop("observations", [])
        source_timestamp = record.pop("source_timestamp", None)
        identity = {key: record.pop(key) for key in ("platform", "canonical_id")}
        candidate, created = VideoCandidate.objects.get_or_create(
            **identity, defaults=record
        )
        # Preserve administrator decisions, rights, and manual category edits on refresh.
        if not created:
            candidate = VideoCandidate.objects.select_for_update().get(pk=candidate.pk)
            candidate.signals = record.get("signals", candidate.signals)
            candidate.safety_flags = sorted(
                set(candidate.safety_flags + record.get("safety_flags", []))
            )
            if candidate.safety_flags and candidate.review_status == "approved":
                candidate.review_status = "pending"
            candidate.save(update_fields=["signals", "safety_flags", "review_status"])
        CandidateDiscovery.objects.get_or_create(
            candidate=candidate,
            run=run,
            defaults={
                "source_timestamp": source_timestamp,
                "metadata": {
                    "kind": provider.kind,
                    "language": record.get("language", ""),
                    "signals": record.get("signals", {}),
                },
            },
        )
        for obs in observations:
            observed_at = obs.pop("observed_at")
            EngagementSnapshot.objects.get_or_create(
                candidate=candidate,
                provider=provider,
                observed_at=observed_at,
                defaults=obs,
            )
        for kind, key in [
            ("topic", "topics"),
            ("hashtag", "hashtags"),
            ("sound", "sounds"),
        ]:
            for value in record.get("signals", {}).get(key, []):
                signal, _ = TrendSignal.objects.get_or_create(
                    kind=kind, value=value.casefold()
                )
                signal.candidates.add(candidate)
                signal.save(update_fields=["last_seen"])
                if kind == "topic":
                    cluster, _ = TrendCluster.objects.get_or_create(
                        name=value.casefold()
                    )
                    cluster.candidates.add(candidate)
                    count = cluster.candidates.count()
                    cluster.lifecycle = (
                        "saturated"
                        if count >= 20
                        else "peak"
                        if count >= 10
                        else "rising"
                        if count >= 3
                        else "emerging"
                    )
                    cluster.save()
        score_candidate(candidate)
    return len(serializer.validated_data)


def run_discovery(provider):
    run = DiscoveryRun.objects.create(provider=provider)
    try:
        from .browser_provider import PlaywrightTrendProvider

        adapter = {
            "fixture": FixtureProvider,
            "feed": AuthorizedFeedProvider,
            "browser": PlaywrightTrendProvider,
        }.get(provider.kind)
        if adapter is None:
            raise ValueError("Manual providers use the import endpoint.")
        run.candidates_seen = ingest(provider, run, adapter().discover())
        run.status = "success"
        provider.last_success = timezone.now()
        provider.save(update_fields=["last_success"])
    except Exception as exc:
        run.status = "failed"
        # Never persist provider URLs, response bodies, or credentials in error messages.
        from .browser_provider import DiscoveryAccessError

        run.error = (
            str(exc)[:500]
            if isinstance(exc, DiscoveryAccessError)
            else f"{type(exc).__name__}: provider ingestion failed; check configuration and feed schema."
        )
    run.finished_at = timezone.now()
    run.save()
    return run
