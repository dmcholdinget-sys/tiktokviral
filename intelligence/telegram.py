import secrets
from datetime import timedelta
import requests
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from .models import TelegramDelivery, DistributionAssignment
from .services import audit


def bot_request(method, payload):
    if not settings.TELEGRAM_BOT_TOKEN:
        raise ValueError("Telegram bot token is not configured.")
    response = requests.post(
        f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/{method}",
        json=payload,
        timeout=(5, 20),
    )
    data = response.json()
    return data


def deliver(delivery_id):
    with transaction.atomic():
        delivery = (
            TelegramDelivery.objects.select_for_update()
            .select_related("assignment__candidate", "assignment__publisher")
            .get(pk=delivery_id)
        )
        assignment = DistributionAssignment.objects.select_for_update().get(
            pk=delivery.assignment_id
        )
        if delivery.status not in ("pending", "retry") or assignment.status != "queued":
            return delivery.status
        if delivery.next_attempt_at and delivery.next_attempt_at > timezone.now():
            return delivery.status
        if assignment.candidate.review_status != "approved":
            return "not_approved"
        chat = assignment.publisher.telegram_chat_id
        if not chat or not settings.TELEGRAM_BOT_TOKEN:
            delivery.error = "Awaiting publisher chat binding or bot configuration."
            delivery.save(update_fields=["error"])
            return "blocked"
        delivery.status = "sending"
        delivery.attempts += 1
        delivery.save()
        candidate = assignment.candidate
        text = f"{candidate.title}\n{candidate.url}\nScore: {candidate.score if candidate.score is not None else 'unavailable'} · {candidate.confidence} confidence\nLink-only opportunity. Create an original response or use media with documented permission.\nAssignment #{assignment.pk}"
        payload = {
            "chat_id": chat,
            "text": text[:4000],
            "reply_markup": {
                "inline_keyboard": [
                    [
                        {"text": "Accept", "callback_data": f"accept:{assignment.pk}"},
                        {
                            "text": "Decline",
                            "callback_data": f"decline:{assignment.pk}",
                        },
                    ]
                ]
            },
        }
    try:
        data = bot_request("sendMessage", payload)
    except Exception:
        # A timeout may mean Telegram accepted the request. Do not blindly duplicate it.
        with transaction.atomic():
            delivery = TelegramDelivery.objects.select_for_update().get(pk=delivery_id)
            delivery.status = "unknown"
            delivery.error = (
                "Delivery outcome uncertain. Reconcile in Telegram before retrying."
            )
            delivery.save()
        return "unknown"
    with transaction.atomic():
        delivery = TelegramDelivery.objects.select_for_update().get(pk=delivery_id)
        assignment = DistributionAssignment.objects.select_for_update().get(
            pk=delivery.assignment_id
        )
        if data.get("ok"):
            delivery.status = "sent"
            delivery.message_id = str(data["result"]["message_id"])
            delivery.sent_at = timezone.now()
            delivery.error = ""
            if assignment.status == "queued":
                assignment.status = "sent"
                assignment.save()
            audit(
                None, "telegram_sent", assignment, {"message_id": delivery.message_id}
            )
        else:
            code = data.get("error_code")
            retryable = code == 429 or isinstance(code, int) and code >= 500
            delivery.status = (
                "retry" if retryable and delivery.attempts < 5 else "failed"
            )
            delay = min(
                3600,
                max(
                    30,
                    int(
                        data.get("parameters", {}).get(
                            "retry_after", 30 * 2**delivery.attempts
                        )
                    ),
                ),
            )
            delivery.next_attempt_at = timezone.now() + timedelta(seconds=delay)
            delivery.error = f"Telegram rejected delivery (code {code})."
        delivery.save()
    return delivery.status
