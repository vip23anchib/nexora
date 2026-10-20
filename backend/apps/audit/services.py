from .models import AuditEvent

SENSITIVE_KEYS = {"password", "token", "secret", "authorization", "refresh", "api_key"}


def sanitize_metadata(data):
    """Recursively redacts sensitive keys from audit metadata."""
    if not isinstance(data, dict):
        return data
    cleaned = {}
    for k, v in data.items():
        if any(sens in k.lower() for sens in SENSITIVE_KEYS):
            cleaned[k] = "[REDACTED]"
        elif isinstance(v, dict):
            cleaned[k] = sanitize_metadata(v)
        else:
            cleaned[k] = v
    return cleaned


def record_audit_event(request, action, resource_type, resource_id, metadata=None):
    """
    Creates an immutable AuditEvent from the active request context.
    """
    actor = getattr(request, "user", None) if request and request.user.is_authenticated else None
    organization = getattr(request, "tenant", None)
    request_id = getattr(request, "request_id", "") if request else ""

    sanitized = sanitize_metadata(metadata or {})

    return AuditEvent.objects.create(
        organization=organization,
        actor=actor,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id),
        request_id=request_id,
        metadata=sanitized,
    )
