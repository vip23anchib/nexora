from apps.common.permissions import IsOperatorOrAdmin, IsTenantMember
from apps.common.views import TenantContextMixin
from django.db import models
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import DatasetSchema
from .serializers import (
    DatasetSchemaSerializer,
    ValidateSampleSerializer,
)


class DatasetSchemaViewSet(TenantContextMixin, viewsets.ModelViewSet):
    """
    CRUD API for dataset schemas, field configuration, and sample validation testing.
    """

    serializer_class = DatasetSchemaSerializer
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]
    filterset_fields = ["status"]
    search_fields = ["name", "slug", "description"]
    ordering_fields = ["name", "version", "created_at"]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated(), IsTenantMember(), IsOperatorOrAdmin()]
        return super().get_permissions()

    def get_queryset(self):
        tenant = getattr(self.request, "tenant", None)
        if not tenant:
            return DatasetSchema.objects.none()
        return (
            DatasetSchema.objects.filter(organization=tenant)
            .prefetch_related("fields")
            .annotate(records_count=models.Count("records", distinct=True))
            .order_by("-created_at")
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["organization"] = getattr(self.request, "tenant", None)
        context["user"] = self.request.user
        return context

    @extend_schema(
        summary="Validate sample CSV/JSON payload against schema",
        request=ValidateSampleSerializer,
        responses={200: ValidateSampleSerializer},
    )
    @action(detail=True, methods=["post"], url_path="validate-sample")
    def validate_sample(self, request, pk=None):
        schema = self.get_object()
        serializer = ValidateSampleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.validate_sample(schema)
        return Response(result, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Get version history of this schema",
        responses={200: DatasetSchemaSerializer(many=True)},
    )
    @action(detail=True, methods=["get"], url_path="versions")
    def versions(self, request, pk=None):
        schema = self.get_object()
        versions = (
            DatasetSchema.objects.filter(
                organization=request.tenant,
                slug=schema.slug,
            )
            .prefetch_related("fields")
            .order_by("-version")
        )
        serializer = self.get_serializer(versions, many=True)
        return Response(serializer.data)
