from django.core.management.base import BaseCommand, CommandError
from intelligence.models import DiscoveryProvider
from intelligence.providers import run_discovery


class Command(BaseCommand):
    help = "Run enabled authorized providers (or explicitly select a provider ID)."

    def add_arguments(self, parser):
        parser.add_argument("--provider", type=int)

    def handle(self, *args, **options):
        providers = (
            DiscoveryProvider.objects.filter(pk=options["provider"])
            if options["provider"]
            else DiscoveryProvider.objects.filter(enabled=True).exclude(kind="manual")
        )
        if not providers.exists():
            raise CommandError("No provider selected or enabled.")
        failed = False
        for provider in providers:
            run = run_discovery(provider)
            self.stdout.write(f"{provider.name}: {run.status} ({run.candidates_seen})")
            failed |= run.status != "success"
        if failed:
            raise CommandError("Provider failed. Inspect discovery run status.")
