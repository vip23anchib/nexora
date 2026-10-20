from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import WorkflowEventViewSet

app_name = "workflows"

router = DefaultRouter()
router.register(r"events", WorkflowEventViewSet, basename="workflow-events")

urlpatterns = [
    path("", include(router.urls)),
]
