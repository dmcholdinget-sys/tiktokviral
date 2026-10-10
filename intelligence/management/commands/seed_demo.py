from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from intelligence.models import DiscoveryProvider, PublisherProfile, RankingModelVersion
from intelligence.providers import run_discovery
from intelligence.ranking import DEFAULT_WEIGHTS, DEFAULT_BENCHMARKS


class Command(BaseCommand):
    help = "Load explicitly labeled fixture data. Does not create credentials or enable live discovery."

    def handle(self, *args, **options):
        RankingModelVersion.objects.get_or_create(
            version="baseline-v1",
            defaults={
                "weights": DEFAULT_WEIGHTS,
                "benchmarks": DEFAULT_BENCHMARKS,
                "active": True,
                "evidence": {"status": "Unvalidated initial hypothesis"},
            },
        )
        DiscoveryProvider.objects.get_or_create(
            name="Public trends · Playwright",
            defaults={
                "kind": "browser",
                "enabled": True,
                "capabilities": {
                    "regions": ["ET relevance filtering; platform coverage unverified"],
                    "methods": ["public trends", "topic search"],
                    "limitations": ["No CAPTCHA bypass", "Metrics may be unavailable"],
                },
            },
        )
        Group.objects.get_or_create(name="Analyst")
        provider, _ = DiscoveryProvider.objects.get_or_create(
            name="Fixture demo (not live)",
            defaults={
                "kind": "fixture",
                "enabled": False,
                "capabilities": {
                    "regions": ["ET"],
                    "methods": ["fixture"],
                    "freshness": "synthetic",
                },
            },
        )
        DiscoveryProvider.objects.get_or_create(
            name="Authorized JSON feed", defaults={"kind": "feed", "enabled": False}
        )
        for index in range(1, 5):
            user, created = User.objects.get_or_create(username=f"publisher{index}")
            if created:
                user.set_unusable_password()
                user.save()
            PublisherProfile.objects.get_or_create(
                user=user, defaults={"display_name": f"Family publisher {index}"}
            )
        run = run_discovery(provider)
        self.stdout.write(
            f"Demo run: {run.status}; {run.candidates_seen} record(s). Publisher passwords remain unset."
        )
