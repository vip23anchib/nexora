from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import OrganizationDetailView, OrganizationMembershipViewSet

app_name = "organizations"

router = DefaultRouter()
router.register(r"members", OrganizationMembershipViewSet, basename="organization-members")

urlpatterns = [
    path("", OrganizationDetailView.as_view(), name="organization-detail"),
    path("", include(router.urls)),
]
