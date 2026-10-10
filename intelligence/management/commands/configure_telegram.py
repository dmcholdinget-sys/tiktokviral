"""Register an HTTPS webhook without exposing bot credentials in shell arguments."""

from urllib.parse import urlsplit
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from intelligence.telegram import bot_request


class Command(BaseCommand):
    help = "Register the Telegram webhook using environment credentials."

    def add_arguments(self, parser):
        parser.add_argument("--webhook-url", required=True)

    def handle(self, *args, **options):
        url = options["webhook_url"]
        parsed = urlsplit(url)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username
            or parsed.password
        ):
            raise CommandError(
                "Use a public HTTPS webhook URL without embedded credentials."
            )
        if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_WEBHOOK_SECRET:
            raise CommandError(
                "Configure TELEGRAM_BOT_TOKEN and TELEGRAM_WEBHOOK_SECRET securely first."
            )
        try:
            result = bot_request(
                "setWebhook",
                {
                    "url": url,
                    "secret_token": settings.TELEGRAM_WEBHOOK_SECRET,
                    "allowed_updates": ["message", "callback_query"],
                },
            )
        except Exception:
            raise CommandError(
                "Telegram registration failed; check network access and credentials."
            ) from None
        if not result.get("ok"):
            raise CommandError(
                "Telegram rejected webhook registration; check deployment and credentials."
            )
        self.stdout.write("Telegram webhook registered.")
