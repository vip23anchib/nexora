from apps.common.permissions import IsTenantMember
from apps.common.views import TenantContextMixin
from rest_framework import permissions, viewsets

from .models import WorkflowEvent
from .serializers import WorkflowEventSerializer


class WorkflowEventViewSet(TenantContextMixin, viewsets.ReadOnlyModelViewSet):
    """
    Query and inspect the auditable state transition timeline for workflow tasks.
    """

    serializer_class = WorkflowEventSerializer
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]
    filterset_fields = ["import_job", "event_type", "previous_state", "new_state"]
    ordering_fields = ["created_at"]

    def get_queryset(self):
        tenant = getattr(self.request, "tenant", None)
        if not tenant:
            return WorkflowEvent.objects.none()
        return WorkflowEvent.objects.filter(organization=tenant).select_related("import_job").order_by("-created_at")
