from apps.common.permissions import IsTenantMember
from apps.common.views import TenantContextMixin
from rest_framework import permissions, viewsets

from .models import ImportedRecord
from .serializers import ImportedRecordSerializer


class ImportedRecordViewSet(TenantContextMixin, viewsets.ReadOnlyModelViewSet):
    """
    Query, filter, and inspect validated data records scoped to the tenant.
    """

    serializer_class = ImportedRecordSerializer
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]
    filterset_fields = ["dataset_schema", "source_job", "external_id"]
    search_fields = ["external_id", "record_hash"]
    ordering_fields = ["created_at", "source_row_number"]

    def get_queryset(self):
        tenant = getattr(self.request, "tenant", None)
        if not tenant:
            return ImportedRecord.objects.none()
        return (
            ImportedRecord.objects.filter(organization=tenant)
            .select_related("dataset_schema", "source_job")
            .order_by("-created_at")
        )
