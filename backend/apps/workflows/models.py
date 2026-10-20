from apps.common.models import TenantScopedModel
from apps.ingestion.models import ImportJob
from django.db import models


class WorkflowEvent(TenantScopedModel):
    """
    Durable, auditable log of state transitions and processing events for workflow tasks.
    """

    import_job = models.ForeignKey(
        ImportJob,
        on_delete=models.CASCADE,
        related_name="workflow_events",
        db_index=True,
    )
    event_type = models.CharField(max_length=50, db_index=True)
    previous_state = models.CharField(max_length=30)
    new_state = models.CharField(max_length=30)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Contextual details (e.g. processed rows, trigger actor, retry reason).",
    )

    class Meta(TenantScopedModel.Meta):
        indexes = [
            models.Index(fields=["organization", "-created_at"]),
            models.Index(fields=["import_job", "-created_at"]),
            models.Index(fields=["organization", "event_type"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"Job {self.import_job_id}: {self.previous_state} -> {self.new_state} ({self.event_type})"
