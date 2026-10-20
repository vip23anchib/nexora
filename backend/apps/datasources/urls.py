from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DataSourceViewSet

app_name = "datasources"

router = DefaultRouter()
router.register(r"", DataSourceViewSet, basename="data-sources")

urlpatterns = [
    path("", include(router.urls)),
]
