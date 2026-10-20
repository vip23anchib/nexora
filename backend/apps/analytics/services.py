from datetime import timedelta

from apps.ingestion.models import ImportJob, ImportRowError
from apps.schemas.models import DatasetSchema
from django.db.models import Count, F, Q, Sum
from django.utils import timezone


def get_dashboard_analytics(organization):
    """
    Computes high-level operational KPIs for the tenant using single-pass SQL aggregations.
    """
    jobs_qs = ImportJob.objects.filter(organization=organization)

    aggregates = jobs_qs.aggregate(
        total_jobs=Count("id"),
        successful_jobs=Count("id", filter=Q(status=ImportJob.Status.COMPLETED)),
        failed_jobs=Count("id", filter=Q(status=ImportJob.Status.FAILED)),
        partial_jobs=Count("id", filter=Q(status=ImportJob.Status.COMPLETED_WITH_ERRORS)),
        processing_jobs=Count("id", filter=Q(status=ImportJob.Status.PROCESSING)),
        total_records_sum=Sum("total_rows"),
        successful_records_sum=Sum("successful_rows"),
        failed_records_sum=Sum("failed_rows"),
    )

    total_jobs = aggregates["total_jobs"] or 0
    successful_jobs = aggregates["successful_jobs"] or 0
    failed_jobs = aggregates["failed_jobs"] or 0
    partial_jobs = aggregates["partial_jobs"] or 0
    processing_jobs = aggregates["processing_jobs"] or 0

    total_records = aggregates["total_records_sum"] or 0
    successful_records = aggregates["successful_records_sum"] or 0
    failed_records = aggregates["failed_records_sum"] or 0

    # Calculated rates
    validation_failure_rate = 0.0
    if total_records > 0:
        validation_failure_rate = round((failed_records / total_records) * 100, 2)

    # Average processing duration for completed jobs
    completed_jobs = jobs_qs.filter(
        status__in=[ImportJob.Status.COMPLETED, ImportJob.Status.COMPLETED_WITH_ERRORS],
        started_at__isnull=False,
        completed_at__isnull=False,
    )

    durations = [
        (j.completed_at - j.started_at).total_seconds() for j in completed_jobs[:50] if j.completed_at and j.started_at
    ]
    avg_duration = round(sum(durations) / len(durations), 2) if durations else 0.0

    recent_jobs = (
        jobs_qs.select_related("dataset_schema", "created_by")
        .annotate(schema_name=F("dataset_schema__name"))
        .order_by("-created_at")[:5]
        .values(
            "id",
            "file_name",
            "status",
            "total_rows",
            "successful_rows",
            "failed_rows",
            "created_at",
            "schema_name",
        )
    )

    return {
        "total_jobs": total_jobs,
        "successful_jobs": successful_jobs,
        "failed_jobs": failed_jobs,
        "partial_jobs": partial_jobs,
        "processing_jobs": processing_jobs,
        "total_records": total_records,
        "successful_records": successful_records,
        "failed_records": failed_records,
        "validation_failure_rate": validation_failure_rate,
        "avg_duration_seconds": avg_duration,
        "active_schemas_count": DatasetSchema.objects.filter(organization=organization).count(),
        "recent_jobs": list(recent_jobs),
    }


def get_ingestion_trends(organization, days=7):
    """
    Computes daily throughput and error distribution over the specified lookback window.
    """
    now = timezone.now()
    start_date = now - timedelta(days=days)

    jobs = ImportJob.objects.filter(
        organization=organization,
        created_at__gte=start_date,
    ).order_by("created_at")

    # Group by date
    daily_stats = {}
    for i in range(days + 1):
        d_str = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
        daily_stats[d_str] = {
            "date": d_str,
            "jobs_count": 0,
            "successful_records": 0,
            "failed_records": 0,
        }

    for job in jobs:
        d_str = job.created_at.strftime("%Y-%m-%d")
        if d_str in daily_stats:
            daily_stats[d_str]["jobs_count"] += 1
            daily_stats[d_str]["successful_records"] += job.successful_rows
            daily_stats[d_str]["failed_records"] += job.failed_rows

    return list(daily_stats.values())


def get_failure_distribution(organization):
    """
    Groups row errors by error_code to uncover systemic data quality defects.
    """
    breakdown = (
        ImportRowError.objects.filter(organization=organization)
        .values("error_code")
        .annotate(count=Count("id"))
        .order_by("-count")[:10]
    )
    return list(breakdown)


def get_processing_performance(organization):
    """
    Calculates execution speed and latency distribution across completed ingestion batches.
    """
    completed_jobs = ImportJob.objects.filter(
        organization=organization,
        status__in=[ImportJob.Status.COMPLETED, ImportJob.Status.COMPLETED_WITH_ERRORS],
        started_at__isnull=False,
        completed_at__isnull=False,
    )

    durations = [
        (j.completed_at - j.started_at).total_seconds() for j in completed_jobs if j.completed_at and j.started_at
    ]

    if not durations:
        return {
            "total_sampled": 0,
            "avg_duration": 0.0,
            "median_duration": 0.0,
            "min_duration": 0.0,
            "max_duration": 0.0,
        }

    durations.sort()
    n = len(durations)
    median = durations[n // 2] if n % 2 != 0 else (durations[n // 2 - 1] + durations[n // 2]) / 2.0

    return {
        "total_sampled": n,
        "avg_duration": round(sum(durations) / n, 2),
        "median_duration": round(median, 2),
        "min_duration": round(min(durations), 2),
        "max_duration": round(max(durations), 2),
    }


def get_schema_usage(organization):
    """
    Computes volume and job distribution grouped by dataset schema.
    """
    schemas = (
        DatasetSchema.objects.filter(organization=organization)
        .annotate(
            jobs_count=Count("import_jobs", distinct=True),
            records_count=Count("records", distinct=True),
        )
        .order_by("-records_count")
    )

    return [
        {
            "schema_id": str(s.id),
            "name": s.name,
            "slug": s.slug,
            "version": s.version,
            "status": s.status,
            "jobs_count": s.jobs_count,
            "records_count": s.records_count,
        }
        for s in schemas
    ]
