from apps.common.models import TenantScopedModel
from django.conf import settings
from django.db import models


class Notification(TenantScopedModel):
    """
    Operational alerts and status updates delivered to users within a tenant.
    """

    class NotificationType(models.TextChoices):
        JOB_COMPLETED = "job_completed", "Job Completed"
        JOB_FAILED = "job_failed", "Job Failed"
        SCHEMA_UPDATE = "schema_update", "Schema Update"
        SYSTEM_ALERT = "system_alert", "System Alert"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
        db_index=True,
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=50,
        choices=NotificationType.choices,
        default=NotificationType.JOB_COMPLETED,
        db_index=True,
    )
    is_read = models.BooleanField(default=False, db_index=True)
    link = models.CharField(max_length=255, blank=True)

    class Meta(TenantScopedModel.Meta):
        indexes = [
            models.Index(fields=["user", "is_read", "-created_at"]),
            models.Index(fields=["organization", "-created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({'Read' if self.is_read else 'Unread'})"
