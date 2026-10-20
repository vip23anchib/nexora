from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DatasetSchemaViewSet

app_name = "schemas"

router = DefaultRouter()
router.register(r"", DatasetSchemaViewSet, basename="schemas")

urlpatterns = [
    path("", include(router.urls)),
]
