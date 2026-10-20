from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ImportedRecordViewSet

app_name = "records"

router = DefaultRouter()
router.register(r"", ImportedRecordViewSet, basename="records")

urlpatterns = [
    path("", include(router.urls)),
]
