from apps.common.models import TenantScopedModel
from apps.datasources.models import DataSource
from apps.schemas.models import DatasetSchema
from django.conf import settings
from django.db import models


class ImportJob(TenantScopedModel):
    """
    Authoritative state record for an individual data ingestion task.
    """

    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        COMPLETED_WITH_ERRORS = "completed_with_errors", "Completed with Errors"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    dataset_schema = models.ForeignKey(
        DatasetSchema,
        on_delete=models.PROTECT,
        related_name="import_jobs",
        db_index=True,
    )
    schema_version = models.PositiveIntegerField(default=1)
    data_source = models.ForeignKey(
        DataSource,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="import_jobs",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="submitted_import_jobs",
    )
    file_name = models.CharField(max_length=255)
    file_size = models.BigIntegerField(default=0)
    checksum = models.CharField(max_length=64, db_index=True, help_text="SHA-256 hash of raw input file.")
    idempotency_key = models.CharField(max_length=128, null=True, blank=True, db_index=True)
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.QUEUED,
        db_index=True,
    )
    total_rows = models.PositiveIntegerField(default=0)
    processed_rows = models.PositiveIntegerField(default=0)
    successful_rows = models.PositiveIntegerField(default=0)
    failed_rows = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_summary = models.TextField(blank=True)

    class Meta(TenantScopedModel.Meta):
        indexes = [
            models.Index(fields=["organization", "status", "-created_at"]),
            models.Index(fields=["organization", "checksum"]),
            models.Index(fields=["organization", "idempotency_key"]),
        ]

    def __str__(self):
        return f"Job {self.id} [{self.status}] - {self.file_name}"

    @property
    def duration_seconds(self):
        if self.started_at and self.completed_at:
            return round((self.completed_at - self.started_at).total_seconds(), 2)
        return None


class ImportRowError(TenantScopedModel):
    """
    Captures granular row-level validation errors encountered during CSV ingestion.
    """

    import_job = models.ForeignKey(
        ImportJob,
        on_delete=models.CASCADE,
        related_name="row_errors",
        db_index=True,
    )
    row_number = models.PositiveIntegerField(db_index=True)
    field_name = models.CharField(max_length=100, blank=True)
    error_code = models.CharField(max_length=50, db_index=True)
    error_message = models.TextField()

    class Meta(TenantScopedModel.Meta):
        indexes = [
            models.Index(fields=["import_job", "row_number"]),
            models.Index(fields=["organization", "error_code"]),
        ]
        ordering = ["row_number", "id"]

    def __str__(self):
        return f"Job {self.import_job_id} Row {self.row_number}: {self.error_code}"
