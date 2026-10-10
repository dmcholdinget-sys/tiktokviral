from urllib.parse import urlsplit
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError, PermissionDenied
from .models import *
from .ranking import score_candidate


def audit(actor, action, obj, details=None):
    AuditLog.objects.create(
        actor=actor,
        action=action,
        object_type=obj.__class__.__name__,
        object_id=str(obj.pk),
        details=details or {},
    )


def safe_url(value):
    parsed = urlsplit(value)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
    ):
        raise ValidationError(
            "A public HTTPS URL without embedded credentials is required."
        )
    return value


def can_use_media(candidate):
    return (
        candidate.review_status == "approved"
        and candidate.rights in ("owned", "licensed", "permission")
        and bool(candidate.rights_evidence.strip())
        and (
            not candidate.rights_expires_at
            or candidate.rights_expires_at > timezone.now()
        )
    )


@transaction.atomic
def review(candidate, actor, decision, notes="", rights=None, evidence=None):
    if not actor.is_staff:
        raise PermissionDenied
    candidate = VideoCandidate.objects.select_for_update().get(pk=candidate.pk)
    if decision not in ("approved", "rejected"):
        raise ValidationError("Choose approved or rejected.")
    if decision == "approved" and candidate.safety_flags and not notes.strip():
        raise ValidationError(
            "Document your review of the safety flags before approval."
        )
    if rights is not None:
        if rights not in dict(VideoCandidate._meta.get_field("rights").choices):
            raise ValidationError("Invalid rights status.")
        candidate.rights = rights
        candidate.rights_evidence = evidence or ""
    candidate.review_status = decision
    candidate.save()
    ContentReview.objects.create(
        candidate=candidate, reviewer=actor, decision=decision, notes=notes
    )
    audit(actor, "review", candidate, {"decision": decision, "notes": notes})
    return candidate


@transaction.atomic
def assign(candidate, publisher, actor):
    if not actor.is_staff:
        raise PermissionDenied
    candidate = VideoCandidate.objects.select_for_update().get(pk=candidate.pk)
    publisher = PublisherProfile.objects.select_for_update().get(pk=publisher.pk)
    if candidate.review_status != "approved":
        raise ValidationError("Only approved candidates may be assigned.")
    if not publisher.active or not publisher.user.is_active:
        raise ValidationError("Publisher is inactive.")
    existing = DistributionAssignment.objects.filter(
        candidate=candidate, publisher=publisher
    ).first()
    if existing:
        return existing, False
    today = timezone.localdate()
    if (
        publisher.assignments.filter(created_at__date=today)
        .exclude(status="revoked")
        .count()
        >= publisher.daily_limit
    ):
        raise ValidationError("Publisher daily assignment limit reached.")
    assignment = DistributionAssignment.objects.create(
        candidate=candidate, publisher=publisher, assigned_by=actor
    )
    TelegramDelivery.objects.create(assignment=assignment)
    Notification.objects.get_or_create(
        key=f"assignment:{assignment.pk}",
        defaults={
            "user": publisher.user,
            "message": f"New opportunity: {candidate.title}"[:500],
            "path": f"/assignments/{assignment.pk}/",
        },
    )
    audit(actor, "assign", assignment)
    return assignment, True


@transaction.atomic
def transition(assignment, actor, status):
    assignment = DistributionAssignment.objects.select_for_update().get(
        pk=assignment.pk
    )
    if status == "revoked":
        if not actor.is_staff:
            raise PermissionDenied
        if assignment.status == "published":
            raise ValidationError("Published assignments cannot be revoked.")
    else:
        if assignment.publisher.user_id != actor.pk:
            raise PermissionDenied
        allowed = {
            "accepted": ("queued", "sent"),
            "declined": ("queued", "sent", "accepted"),
        }
        if status not in allowed or assignment.status not in allowed[status]:
            raise ValidationError("Invalid assignment transition.")
    assignment.status = status
    assignment.save()
    audit(actor, "assignment_" + status, assignment)
    return assignment


@transaction.atomic
def publish(assignment, actor, url, published_at):
    assignment = DistributionAssignment.objects.select_for_update().get(
        pk=assignment.pk
    )
    if assignment.publisher.user_id != actor.pk:
        raise PermissionDenied
    if assignment.status != "accepted":
        raise ValidationError("Accept the assignment before reporting publication.")
    if published_at > timezone.now():
        raise ValidationError("Publication time cannot be in the future.")
    safe_url(url)
    post = PublishedPost.objects.create(
        assignment=assignment, url=url, published_at=published_at
    )
    assignment.status = "published"
    assignment.save()
    audit(actor, "publish", post)
    return post


@transaction.atomic
def reconcile_delivery(delivery, actor, resolution, note):
    if not actor.is_staff:
        raise PermissionDenied
    if not note.strip():
        raise ValidationError("Document your Telegram reconciliation.")
    delivery = TelegramDelivery.objects.select_for_update().get(pk=delivery.pk)
    assignment = DistributionAssignment.objects.select_for_update().get(
        pk=delivery.assignment_id
    )
    if delivery.status not in ("failed", "unknown", "sending"):
        raise ValidationError("Only failed or uncertain deliveries can be reconciled.")
    if assignment.status != "queued":
        raise ValidationError("Assignment is no longer queued.")
    if resolution == "sent":
        delivery.status = "sent"
        delivery.sent_at = timezone.now()
        assignment.status = "sent"
        assignment.save()
    elif resolution == "retry":
        delivery.status = "pending"
        delivery.next_attempt_at = None
        delivery.attempts = 0
    else:
        raise ValidationError("Choose sent or retry.")
    delivery.error = ""
    delivery.save()
    audit(
        actor, "delivery_reconciled", delivery, {"resolution": resolution, "note": note}
    )
