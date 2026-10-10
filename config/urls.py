from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from intelligence import views, api

router = DefaultRouter()
router.register("candidates", api.CandidateViewSet, basename="candidate")
router.register("assignments", api.AssignmentViewSet, basename="assignment")
router.register("posts", api.PostViewSet, basename="post")
router.register("metrics", api.MetricViewSet, basename="metric")
urlpatterns = [
    path(
        "notifications/<int:pk>/read/",
        views.notification_read,
        name="notification-read",
    ),
    path("reports/export/", views.export_report, name="export-report"),
    path("deliveries/<int:pk>/reconcile/", views.reconcile, name="reconcile"),
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("api/", include(router.urls)),
    path("", views.dashboard, name="dashboard"),
    path("candidates/", views.candidates, name="candidates"),
    path("candidates/<int:pk>/", views.candidate_detail, name="candidate-detail"),
    path("assignments/", views.assignments, name="assignments"),
    path("assignments/<int:pk>/", views.assignment_detail, name="assignment-detail"),
    path("trends/", views.trends, name="trends"),
    path("reports/", views.reports, name="reports"),
    path("reports/metrics/<int:pk>/verify/", views.verify_metric, name="verify-metric"),
    path("integrations/", views.integrations, name="integrations"),
    path("integrations/<int:pk>/discover/", views.discover, name="discover"),
    path("media/<int:pk>/", views.private_media, name="private-media"),
    path("telegram/webhook/", views.telegram_webhook, name="telegram-webhook"),
]
