from .authentication import resolve_tenant_context


class TenantContextMixin:
    """Mixin for API views and viewsets to guarantee request.tenant and request.membership are resolved."""

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        tenant, membership = resolve_tenant_context(request)
        request.tenant = tenant
        request.membership = membership
