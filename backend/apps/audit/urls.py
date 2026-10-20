from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AuditEventViewSet

app_name = "audit"

router = DefaultRouter()
router.register(r"", AuditEventViewSet, basename="audit-events")

urlpatterns = [
    path("", include(router.urls)),
]
