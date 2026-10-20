import uuid

from apps.organizations.models import Organization
from django.conf import settings
from django.db import models


class AuditEvent(models.Model):
    """
    Immutable audit record documenting all security-relevant, configuration,
    and administrative operational actions.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="audit_events",
        db_index=True,
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_events",
        db_index=True,
    )
    action = models.CharField(max_length=100, db_index=True)
    resource_type = models.CharField(max_length=100, db_index=True)
    resource_id = models.CharField(max_length=100)
    request_id = models.CharField(max_length=64, blank=True, db_index=True)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Sanitized, non-sensitive audit metadata.",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["organization", "-created_at"]),
            models.Index(fields=["organization", "action"]),
            models.Index(fields=["request_id"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        actor_email = self.actor.email if self.actor else "System"
        return f"{self.created_at.strftime('%Y-%m-%d %H:%M:%S')} | {actor_email} | {self.action} on {self.resource_type}:{self.resource_id}"
