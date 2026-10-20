from apps.common.permissions import IsTenantMember
from apps.common.views import TenantContextMixin
from django.db.models import Q
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(TenantContextMixin, viewsets.ReadOnlyModelViewSet):
    """
    List, filter, and mark operational alerts and workflow notices as read.
    """

    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]
    filterset_fields = ["is_read", "notification_type"]
    ordering_fields = ["created_at"]

    def get_queryset(self):
        user = self.request.user
        tenant = getattr(self.request, "tenant", None)
        if not tenant:
            return Notification.objects.none()

        return (
            Notification.objects.filter(organization=tenant)
            .filter(Q(user=user) | Q(user__isnull=True))
            .order_by("-created_at")
        )

    @extend_schema(summary="Get unread notifications count")
    @action(detail=False, methods=["get"], url_path="unread-count")
    def unread_count(self, request):
        count = self.get_queryset().filter(is_read=False).count()
        return Response({"unread_count": count})

    @extend_schema(summary="Mark notification as read")
    @action(detail=True, methods=["post"], url_path="mark-read")
    def mark_read(self, request, pk=None):
        instance = self.get_object()
        instance.is_read = True
        instance.save(update_fields=["is_read", "updated_at"])
        return Response(self.get_serializer(instance).data, status=status.HTTP_200_OK)

    @extend_schema(summary="Mark all unread notifications as read")
    @action(detail=False, methods=["post"], url_path="mark-all-read")
    def mark_all_read(self, request):
        updated = self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({"marked_read_count": updated}, status=status.HTTP_200_OK)
