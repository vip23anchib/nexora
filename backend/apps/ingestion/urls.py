from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ImportJobViewSet

app_name = "ingestion"

router = DefaultRouter()
router.register(r"jobs", ImportJobViewSet, basename="import-jobs")

urlpatterns = [
    path("", include(router.urls)),
]
