from apps.common.permissions import IsOrgAdmin, IsTenantMember
from apps.common.views import TenantContextMixin
from rest_framework import permissions, viewsets

from .models import AuditEvent
from .serializers import AuditEventSerializer


class AuditEventViewSet(TenantContextMixin, viewsets.ReadOnlyModelViewSet):
    """
    Search and inspect historical audit events. Restricted to Organization Administrators.
    """

    serializer_class = AuditEventSerializer
    permission_classes = [permissions.IsAuthenticated, IsTenantMember, IsOrgAdmin]
    filterset_fields = ["action", "resource_type"]
    search_fields = ["action", "resource_type", "resource_id", "request_id"]
    ordering_fields = ["created_at"]

    def get_queryset(self):
        tenant = getattr(self.request, "tenant", None)
        if not tenant:
            return AuditEvent.objects.none()
        return AuditEvent.objects.filter(organization=tenant).select_related("actor").order_by("-created_at")
