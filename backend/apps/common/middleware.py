import uuid

from django.utils.deprecation import MiddlewareMixin

from .authentication import resolve_tenant_context


class RequestIdMiddleware(MiddlewareMixin):
    """Injects and propagates a unique correlation ID per request."""

    def process_request(self, request):
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())
        request.request_id = request_id

    def process_response(self, request, response):
        if hasattr(request, "request_id"):
            response["X-Request-ID"] = request.request_id
        return response


class TenantContextMiddleware(MiddlewareMixin):
    """Resolves and populates tenant context."""

    def process_request(self, request):
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            tenant, membership = resolve_tenant_context(request, user)
            request.tenant = tenant
            request.membership = membership
        else:
            request.tenant = None
            request.membership = None
