import csv
import hashlib
import os

from apps.records.models import ImportedRecord, compute_record_hash
from apps.schemas.models import DatasetSchema
from apps.schemas.validators import validate_row_against_schema
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import ImportJob, ImportRowError

BATCH_SIZE = 500


def compute_stream_checksum_and_size(file_obj):
    """
    Reads file stream in chunks to compute SHA-256 digest and total byte count
    without loading the entire file into memory.
    """
    hasher = hashlib.sha256()
    size = 0
    file_obj.seek(0)
    while chunk := file_obj.read(65536):
        if isinstance(chunk, str):
            chunk = chunk.encode("utf-8")
        hasher.update(chunk)
        size += len(chunk)
    file_obj.seek(0)
    return hasher.hexdigest(), size


def create_import_job(organization, user, schema_id, file_obj, idempotency_key=None, data_source=None):
    """
    Validates file constraints, computes checksum, checks idempotency,
    and creates a queued ImportJob.
    """
    schema = DatasetSchema.objects.filter(organization=organization, id=schema_id).first()
    if not schema:
        raise ValidationError({"schema_id": "Invalid or inaccessible dataset schema."})

    checksum, file_size = compute_stream_checksum_and_size(file_obj)

    max_size = getattr(settings, "MAX_UPLOAD_SIZE_BYTES", 10 * 1024 * 1024)
    if file_size > max_size:
        raise ValidationError(f"File size ({file_size} bytes) exceeds maximum permitted limit ({max_size} bytes).")

    # Idempotency check: look for recent identical upload
    if idempotency_key:
        existing = ImportJob.objects.filter(
            organization=organization,
            idempotency_key=idempotency_key,
        ).first()
        if existing:
            return existing, False

    # Check checksum match within last 24 hours for identical file deduplication
    existing_by_hash = (
        ImportJob.objects.filter(
            organization=organization,
            dataset_schema=schema,
            checksum=checksum,
            status__in=[ImportJob.Status.COMPLETED, ImportJob.Status.PROCESSING, ImportJob.Status.QUEUED],
        )
        .order_by("-created_at")
        .first()
    )

    if existing_by_hash and not idempotency_key:
        # If identical file was uploaded, return existing or allow caller to decide
        return existing_by_hash, False

    # Save file payload to media storage under secure organized path
    ext = os.path.splitext(file_obj.name)[1].lower() or ".csv"
    file_dir = os.path.join(settings.MEDIA_ROOT, "uploads", str(organization.id))
    os.makedirs(file_dir, exist_ok=True)
    temp_file_name = f"{checksum[:16]}_{int(timezone.now().timestamp())}{ext}"
    local_path = os.path.join(file_dir, temp_file_name)

    with open(local_path, "wb") as f:
        file_obj.seek(0)
        while chunk := file_obj.read(65536):
            if isinstance(chunk, str):
                chunk = chunk.encode("utf-8")
            f.write(chunk)

    job = ImportJob.objects.create(
        organization=organization,
        dataset_schema=schema,
        schema_version=schema.version,
        data_source=data_source,
        created_by=user,
        file_name=file_obj.name,
        file_size=file_size,
        checksum=checksum,
        idempotency_key=idempotency_key,
        status=ImportJob.Status.QUEUED,
        error_summary="",
    )

    return job, True


def process_import_job(job_id):
    """
    Executes row-by-row streaming ingestion against schema specifications.
    Uses database row locking on ImportJob to prevent concurrent processing races.
    """
    from apps.workflows.services import transition_job_state

    # Lock and transition to PROCESSING
    try:
        job, _ = transition_job_state(
            job_id,
            ImportJob.Status.PROCESSING,
            event_type="PROCESSING_STARTED",
            metadata={"source": "worker"},
        )
    except Exception:
        # If job is already processing or in an incompatible state, exit safely
        job = ImportJob.objects.filter(id=job_id).first()
        return job

    # Locate uploaded file
    file_dir = os.path.join(settings.MEDIA_ROOT, "uploads", str(job.organization_id))
    local_files = (
        [f for f in os.listdir(file_dir) if f.startswith(job.checksum[:16])] if os.path.exists(file_dir) else []
    )

    if not local_files:
        job.status = ImportJob.Status.FAILED
        job.error_summary = "Ingestion source file not found on disk."
        job.completed_at = timezone.now()
        job.save(update_fields=["status", "error_summary", "completed_at", "updated_at"])
        return job

    file_path = os.path.join(file_dir, local_files[0])
    schema_fields = list(job.dataset_schema.fields.all())

    # Pre-fetch existing record hashes and external_ids for idempotency
    existing_hashes = set(
        ImportedRecord.objects.filter(
            organization=job.organization,
            dataset_schema=job.dataset_schema,
        ).values_list("record_hash", flat=True)
    )

    total_rows = 0
    processed_rows = 0
    successful_rows = 0
    failed_rows = 0

    records_to_create = []
    errors_to_create = []

    try:
        with open(file_path, "r", encoding="utf-8-sig", errors="replace") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                job.status = ImportJob.Status.FAILED
                job.error_summary = "CSV file is empty or missing valid headers."
                job.completed_at = timezone.now()
                job.save(update_fields=["status", "error_summary", "completed_at", "updated_at"])
                return job

            # Check header requirements
            csv_field_names = {col.strip() for col in reader.fieldnames if col}
            required_field_names = {field.field_name for field in schema_fields if field.is_required}

            missing_required = required_field_names - csv_field_names
            if missing_required:
                job.status = ImportJob.Status.FAILED
                job.error_summary = f"Missing required CSV columns: {', '.join(sorted(missing_required))}"
                job.completed_at = timezone.now()
                job.save(update_fields=["status", "error_summary", "completed_at", "updated_at"])
                return job

            for row_idx, raw_row in enumerate(reader, start=1):
                total_rows += 1
                row_dict = {k.strip(): v for k, v in raw_row.items() if k}

                cleaned_payload, row_validation_errors = validate_row_against_schema(
                    schema_fields,
                    row_dict,
                    row_number=row_idx,
                )

                if row_validation_errors:
                    failed_rows += 1
                    for err in row_validation_errors:
                        errors_to_create.append(
                            ImportRowError(
                                organization=job.organization,
                                import_job=job,
                                row_number=row_idx,
                                field_name=err.field_name,
                                error_code=err.error_code,
                                error_message=err.error_message,
                            )
                        )
                else:
                    # Idempotent deduplication check
                    rec_hash = compute_record_hash(cleaned_payload)
                    if rec_hash in existing_hashes:
                        # Skip duplicate record already committed
                        successful_rows += 1
                    else:
                        existing_hashes.add(rec_hash)
                        ext_id = (
                            cleaned_payload.get("candidate_id")
                            or cleaned_payload.get("tracking_number")
                            or cleaned_payload.get("id")
                            or cleaned_payload.get("external_id")
                        )
                        records_to_create.append(
                            ImportedRecord(
                                organization=job.organization,
                                dataset_schema=job.dataset_schema,
                                source_job=job,
                                source_row_number=row_idx,
                                external_id=str(ext_id)[:255] if ext_id else None,
                                payload=cleaned_payload,
                                record_hash=rec_hash,
                            )
                        )
                        successful_rows += 1

                processed_rows += 1

                # Batch flush to avoid memory pressure
                if len(records_to_create) >= BATCH_SIZE:
                    with transaction.atomic():
                        ImportedRecord.objects.bulk_create(records_to_create, batch_size=BATCH_SIZE)
                        records_to_create = []

                if len(errors_to_create) >= BATCH_SIZE:
                    with transaction.atomic():
                        ImportRowError.objects.bulk_create(errors_to_create, batch_size=BATCH_SIZE)
                        errors_to_create = []

        # Final flush of remaining records and errors outside the loop
        with transaction.atomic():
            if records_to_create:
                ImportedRecord.objects.bulk_create(records_to_create, batch_size=BATCH_SIZE)
            if errors_to_create:
                ImportRowError.objects.bulk_create(errors_to_create, batch_size=BATCH_SIZE)

        # Update final state via state machine
        if failed_rows == 0:
            final_status = ImportJob.Status.COMPLETED
            event_type = "PROCESSING_COMPLETED"
        elif successful_rows > 0:
            final_status = ImportJob.Status.COMPLETED_WITH_ERRORS
            event_type = "PROCESSING_COMPLETED_WITH_ERRORS"
        else:
            final_status = ImportJob.Status.FAILED
            event_type = "PROCESSING_FAILED"

        job.total_rows = total_rows
        job.processed_rows = processed_rows
        job.successful_rows = successful_rows
        job.failed_rows = failed_rows
        job.save(
            update_fields=[
                "total_rows",
                "processed_rows",
                "successful_rows",
                "failed_rows",
                "updated_at",
            ]
        )

        transition_job_state(
            job.id,
            final_status,
            event_type=event_type,
            metadata={
                "total_rows": total_rows,
                "successful_rows": successful_rows,
                "failed_rows": failed_rows,
            },
        )
        job.refresh_from_db()
        return job

    except Exception as e:
        job.total_rows = total_rows
        job.processed_rows = processed_rows
        job.successful_rows = successful_rows
        job.failed_rows = failed_rows
        job.error_summary = f"Fatal ingestion exception: {str(e)}"
        job.save(
            update_fields=[
                "total_rows",
                "processed_rows",
                "successful_rows",
                "failed_rows",
                "error_summary",
                "updated_at",
            ]
        )
        try:
            transition_job_state(
                job.id,
                ImportJob.Status.FAILED,
                event_type="FATAL_EXCEPTION",
                metadata={"error": str(e)},
            )
        except Exception:
            pass
        job.refresh_from_db()
        return job


def retry_import_job(job_id, user):
    """
    Initiates an idempotent retry for a job that failed or completed with errors.
    Cleans up old row errors and re-triggers processing safely.
    """
    from apps.workflows.services import transition_job_state

    # Clear existing row errors from previous attempt
    ImportRowError.objects.filter(import_job_id=job_id).delete()

    job, _ = transition_job_state(
        job_id,
        ImportJob.Status.QUEUED,
        event_type="RETRY_TRIGGERED",
        metadata={"user": user.email},
    )

    # Trigger processing synchronously or asynchronously
    return process_import_job(job.id)
