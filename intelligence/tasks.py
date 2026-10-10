from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import DiscoveryProvider, TelegramDelivery, VideoCandidate
from .providers import run_discovery
from .telegram import deliver
from .services import audit


@shared_task
def discover_all():
    from django.db import connection

    results = []
    for provider in DiscoveryProvider.objects.filter(enabled=True).exclude(
        kind="manual"
    ):
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_try_advisory_lock(%s,%s)", [7319, provider.pk])
            locked = cursor.fetchone()[0]
        if not locked:
            continue
        try:
            results.append(run_discovery(provider).status)
        finally:
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_advisory_unlock(%s,%s)", [7319, provider.pk])
    return results


@shared_task
def deliver_pending():
    ids = list(
        TelegramDelivery.objects.filter(
            status__in=["pending", "retry"], assignment__status="queued"
        ).values_list("pk", flat=True)[:100]
    )
    return {str(pk): deliver(pk) for pk in ids}


@shared_task
def expire_candidates():
    count = 0
    for candidate in VideoCandidate.objects.filter(
        published_at__lt=timezone.now() - timedelta(hours=48),
        review_status__in=["pending", "approved"],
    ):
        candidate.review_status = "expired"
        candidate.save(update_fields=["review_status"])
        audit(None, "expired", candidate)
        count += 1
    return count


@shared_task
def readiness_probe():
    return "celery-ready"


@shared_task
def publisher_reminders():
    from .models import DistributionAssignment, Notification

    count = 0
    for assignment in DistributionAssignment.objects.filter(
        status__in=["sent", "accepted"],
        updated_at__lt=timezone.now() - timedelta(hours=24),
    ).select_related("publisher", "candidate"):
        _, created = Notification.objects.get_or_create(
            key=f"reminder:{assignment.pk}:{timezone.localdate()}",
            defaults={
                "user": assignment.publisher.user,
                "message": f"Publishing update requested: {assignment.candidate.title}"[
                    :500
                ],
                "path": f"/assignments/{assignment.pk}/",
            },
        )
        count += int(created)
    return count
