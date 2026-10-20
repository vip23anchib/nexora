from apps.common.permissions import IsOperatorOrAdmin, IsTenantMember
from apps.common.views import TenantContextMixin
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import DataSource
from .serializers import DataSourceSerializer


class DataSourceViewSet(TenantContextMixin, viewsets.ModelViewSet):
    """
    CRUD API for managing ingestion data sources and external connection configs.
    """

    serializer_class = DataSourceSerializer
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]
    filterset_fields = ["source_type", "is_active"]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at"]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy", "deactivate"]:
            return [permissions.IsAuthenticated(), IsTenantMember(), IsOperatorOrAdmin()]
        return super().get_permissions()

    def get_queryset(self):
        tenant = getattr(self.request, "tenant", None)
        if not tenant:
            return DataSource.objects.none()
        return DataSource.objects.filter(organization=tenant).order_by("-created_at")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["organization"] = getattr(self.request, "tenant", None)
        context["user"] = self.request.user
        return context

    @extend_schema(
        summary="Deactivate data source",
        responses={200: DataSourceSerializer},
    )
    @action(detail=True, methods=["post"], url_path="deactivate")
    def deactivate(self, request, pk=None):
        instance = self.get_object()
        instance.is_active = False
        instance.save(update_fields=["is_active", "updated_at"])
        return Response(self.get_serializer(instance).data, status=status.HTTP_200_OK)
