from apps.ingestion.models import ImportJob
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import WorkflowEvent

VALID_STATE_TRANSITIONS = {
    ImportJob.Status.QUEUED: [
        ImportJob.Status.PROCESSING,
        ImportJob.Status.CANCELLED,
    ],
    ImportJob.Status.PROCESSING: [
        ImportJob.Status.COMPLETED,
        ImportJob.Status.COMPLETED_WITH_ERRORS,
        ImportJob.Status.FAILED,
        ImportJob.Status.CANCELLED,
    ],
    ImportJob.Status.COMPLETED_WITH_ERRORS: [
        ImportJob.Status.QUEUED,
    ],
    ImportJob.Status.FAILED: [
        ImportJob.Status.QUEUED,
    ],
    ImportJob.Status.COMPLETED: [],
    ImportJob.Status.CANCELLED: [],
}


def transition_job_state(job_id, new_state, event_type="STATE_TRANSITION", metadata=None):
    """
    Executes an atomic, lock-protected state machine transition on an ImportJob,
    verifying validity and emitting a durable WorkflowEvent.
    """
    if metadata is None:
        metadata = {}

    with transaction.atomic():
        try:
            job = ImportJob.objects.select_for_update(nowait=False).get(id=job_id)
        except ImportJob.DoesNotExist:
            raise ValidationError(f"ImportJob {job_id} not found.")

        current_state = job.status
        allowed_targets = VALID_STATE_TRANSITIONS.get(current_state, [])

        if new_state not in allowed_targets:
            raise ValidationError(
                f"Invalid workflow state transition: cannot move from '{current_state}' to '{new_state}'. "
                f"Allowed target states: {allowed_targets or 'None (terminal state)'}."
            )

        job.status = new_state
        update_fields = ["status", "updated_at"]

        if new_state == ImportJob.Status.PROCESSING and not job.started_at:
            job.started_at = timezone.now()
            update_fields.append("started_at")
        elif new_state in (
            ImportJob.Status.COMPLETED,
            ImportJob.Status.COMPLETED_WITH_ERRORS,
            ImportJob.Status.FAILED,
            ImportJob.Status.CANCELLED,
        ):
            job.completed_at = timezone.now()
            update_fields.append("completed_at")

        job.save(update_fields=update_fields)

        # Create workflow event record
        event = WorkflowEvent.objects.create(
            organization=job.organization,
            import_job=job,
            event_type=event_type,
            previous_state=current_state,
            new_state=new_state,
            metadata=metadata,
        )

        return job, event
