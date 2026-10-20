import uuid

from rest_framework_simplejwt.authentication import JWTAuthentication


def resolve_tenant_context(request, user=None):
    """
    Resolves the active organization (tenant) and membership for a given request and user.
    """
    if user is None:
        user = getattr(request, "user", None)

    # Only use cache if it was resolved for this exact authenticated user
    cached_user = getattr(request, "_tenant_resolved_user", None)
    if cached_user and user and cached_user == user:
        return getattr(request, "_tenant", None), getattr(request, "_membership", None)

    if not user or not user.is_authenticated:
        return None, None

    from apps.organizations.models import OrganizationMembership

    # Check header: check both headers and META
    org_id_header = None
    if hasattr(request, "headers"):
        org_id_header = request.headers.get("X-Organization-Id")
    if not org_id_header and hasattr(request, "META"):
        org_id_header = request.META.get("HTTP_X_ORGANIZATION_ID")

    memberships = OrganizationMembership.objects.filter(
        user=user,
        is_active=True,
        organization__is_active=True,
    ).select_related("organization")

    if org_id_header:
        try:
            target_uuid = uuid.UUID(str(org_id_header).strip())
            matched = memberships.filter(organization_id=target_uuid).first()
            if matched:
                request._tenant = matched.organization
                request._membership = matched
                request._tenant_resolved_user = user
                return request._tenant, request._membership
        except (ValueError, TypeError):
            pass

    first_membership = memberships.first()
    if first_membership:
        request._tenant = first_membership.organization
        request._membership = first_membership
        request._tenant_resolved_user = user
    else:
        request._tenant = None
        request._membership = None
        request._tenant_resolved_user = user

    return request._tenant, request._membership


class TenantJWTAuthentication(JWTAuthentication):
    """
    Custom JWT Authentication that immediately resolves and populates
    request.tenant and request.membership upon successful JWT validation.
    """

    def authenticate(self, request):
        result = super().authenticate(request)
        if result is not None:
            user, token = result
            tenant, membership = resolve_tenant_context(request, user)
            request.tenant = tenant
            request.membership = membership
        return result
