from apps.common.permissions import IsOrgAdmin, IsTenantMember
from apps.common.views import TenantContextMixin
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status, views, viewsets
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response

from .models import OrganizationMembership
from .serializers import (
    AddMemberSerializer,
    OrganizationMembershipSerializer,
    OrganizationSerializer,
    UpdateMemberSerializer,
)


class OrganizationDetailView(TenantContextMixin, views.APIView):
    """View and update details of the currently active tenant organization."""

    permission_classes = [permissions.IsAuthenticated, IsTenantMember]

    @extend_schema(
        summary="Get active organization profile",
        responses={200: OrganizationSerializer},
    )
    def get(self, request):
        tenant = request.tenant
        if not tenant:
            raise NotFound("No active organization resolved.")
        serializer = OrganizationSerializer(tenant)
        return Response(serializer.data)

    @extend_schema(
        summary="Update active organization settings",
        request=OrganizationSerializer,
        responses={200: OrganizationSerializer},
    )
    def patch(self, request):
        if not request.membership or request.membership.role != OrganizationMembership.Role.ORG_ADMIN:
            raise PermissionDenied("Only organization administrators can update settings.")
        tenant = request.tenant
        serializer = OrganizationSerializer(tenant, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class OrganizationMembershipViewSet(TenantContextMixin, viewsets.ModelViewSet):
    """Manage team members and their RBAC roles within the active organization."""

    permission_classes = [permissions.IsAuthenticated, IsTenantMember]
    serializer_class = OrganizationMembershipSerializer

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated(), IsTenantMember(), IsOrgAdmin()]
        return super().get_permissions()

    def get_queryset(self):
        tenant = getattr(self.request, "tenant", None)
        if not tenant:
            return OrganizationMembership.objects.none()
        return (
            OrganizationMembership.objects.filter(
                organization=tenant,
            )
            .select_related("user")
            .order_by("joined_at")
        )

    def create(self, request, *args, **kwargs):
        serializer = AddMemberSerializer(data=request.data, context={"organization": request.tenant})
        serializer.is_valid(raise_exception=True)
        membership = serializer.save()
        return Response(
            OrganizationMembershipSerializer(membership).data,
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = UpdateMemberSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        membership = serializer.save()
        return Response(OrganizationMembershipSerializer(membership).data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Ensure last admin cannot be deleted
        if instance.role == OrganizationMembership.Role.ORG_ADMIN and instance.is_active:
            remaining = (
                OrganizationMembership.objects.filter(
                    organization=instance.organization,
                    role=OrganizationMembership.Role.ORG_ADMIN,
                    is_active=True,
                )
                .exclude(pk=instance.pk)
                .count()
            )
            if remaining == 0:
                return Response(
                    {"detail": "Cannot remove the last administrator of the organization."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
