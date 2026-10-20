import hashlib
import json

from apps.common.models import TenantScopedModel
from apps.ingestion.models import ImportJob
from apps.schemas.models import DatasetSchema
from django.db import models


def compute_record_hash(payload: dict) -> str:
    """Computes a deterministic SHA-256 hash from a dictionary payload."""
    serialized = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class ImportedRecord(TenantScopedModel):
    """
    Stores validated, structured records ingested into the platform.
    """

    dataset_schema = models.ForeignKey(
        DatasetSchema,
        on_delete=models.PROTECT,
        related_name="records",
        db_index=True,
    )
    source_job = models.ForeignKey(
        ImportJob,
        on_delete=models.CASCADE,
        related_name="imported_records",
        db_index=True,
    )
    source_row_number = models.PositiveIntegerField(default=1)
    external_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
        help_text="Optional external identifier used for idempotency and upsert semantics.",
    )
    payload = models.JSONField(help_text="Structured record data matching the dataset schema fields.")
    record_hash = models.CharField(
        max_length=64,
        db_index=True,
        help_text="SHA-256 digest of normalized payload for duplicate detection.",
    )

    class Meta(TenantScopedModel.Meta):
        indexes = [
            models.Index(fields=["organization", "dataset_schema", "-created_at"]),
            models.Index(fields=["organization", "dataset_schema", "external_id"]),
            models.Index(fields=["source_job", "source_row_number"]),
            models.Index(fields=["organization", "record_hash"]),
        ]

    def __str__(self):
        ext = f" [{self.external_id}]" if self.external_id else ""
        return f"Record {self.id}{ext} ({self.dataset_schema.name})"

    def save(self, *args, **kwargs):
        if not self.record_hash and isinstance(self.payload, dict):
            self.record_hash = compute_record_hash(self.payload)
        super().save(*args, **kwargs)
