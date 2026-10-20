from apps.common.models import TenantScopedModel
from django.conf import settings
from django.db import models


class DataSource(TenantScopedModel):
    """
    Represents an ingestion channel or file source configured for an organization.
    """

    class SourceType(models.TextChoices):
        FILE_UPLOAD = "file_upload", "Manual File Upload"
        SFTP = "sftp", "SFTP Server"
        WEBHOOK = "webhook", "Inbound Webhook"

    name = models.CharField(max_length=200)
    source_type = models.CharField(
        max_length=50,
        choices=SourceType.choices,
        default=SourceType.FILE_UPLOAD,
        db_index=True,
    )
    description = models.TextField(blank=True)
    configuration = models.JSONField(
        default=dict,
        blank=True,
        help_text="Safe connection parameters and options (sensitive keys must not be stored in plain text).",
    )
    is_active = models.BooleanField(default=True, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_data_sources",
    )

    class Meta(TenantScopedModel.Meta):
        indexes = [
            models.Index(fields=["organization", "source_type"]),
            models.Index(fields=["organization", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.source_type}) [{self.organization.name}]"
