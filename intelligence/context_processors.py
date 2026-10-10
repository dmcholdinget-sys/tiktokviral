from .models import Notification


def notifications(request):
    if not request.user.is_authenticated:
        return {}
    return {
        "is_analyst": request.user.groups.filter(name="Analyst").exists(),
        "notifications": Notification.objects.filter(
            user=request.user, read=False
        ).order_by("-created_at")[:5],
    }
