from rest_framework import permissions

from .authentication import resolve_tenant_context


class IsTenantMember(permissions.BasePermission):
    """Allows access only to authenticated users with an active organization membership."""

    message = "You are not an active member of this organization."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        tenant = getattr(request, "tenant", None)
        membership = getattr(request, "membership", None)
        if not (tenant and membership):
            tenant, membership = resolve_tenant_context(request)
            request.tenant = tenant
            request.membership = membership
        if tenant and membership and membership.is_active:
            return True
        if getattr(request.user, "is_platform_admin", False):
            return True
        return False


class HasTenantRole(permissions.BasePermission):
    """
    Checks if the user's role in the active organization satisfies the allowed roles.
    """

    allowed_roles = []

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if getattr(request.user, "is_platform_admin", False):
            return True
        membership = getattr(request, "membership", None)
        if not membership:
            tenant, membership = resolve_tenant_context(request)
            request.tenant = tenant
            request.membership = membership
        if not membership or not membership.is_active:
            return False
        allowed = getattr(view, "allowed_roles", self.allowed_roles)
        return membership.role in allowed


class IsOrgAdmin(HasTenantRole):
    allowed_roles = ["org_admin"]


class IsOperatorOrAdmin(HasTenantRole):
    allowed_roles = ["org_admin", "operator"]


class IsAnalystOrAbove(HasTenantRole):
    allowed_roles = ["org_admin", "operator", "analyst"]


class IsViewerOrAbove(HasTenantRole):
    allowed_roles = ["org_admin", "operator", "analyst", "viewer"]


class IsPlatformAdmin(permissions.BasePermission):
    """Allows access only to system/platform administrators."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_platform_admin
        )
