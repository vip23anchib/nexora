import csv
import io
import json

from django.http import HttpResponse

FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def sanitize_csv_value(value):
    """
    Sanitizes values against CSV Formula Injection (CWE-1236).
    If a string starts with formula characters (=, +, -, @), prepends a single quote.
    """
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        value = json.dumps(value, default=str)
    s_val = str(value)
    if s_val.startswith(FORMULA_PREFIXES):
        return f"'{s_val}"
    return s_val


def generate_records_csv_response(records_qs, schema):
    """
    Generates a safe CSV file response for exported tenant records.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Determine headers from schema fields
    fields = list(schema.fields.all().order_by("position"))
    headers = ["record_id", "external_id", "created_at"] + [f.field_name for f in fields]
    writer.writerow([sanitize_csv_value(h) for h in headers])

    for rec in records_qs[:5000]:  # Bound max export size to 5,000 records
        payload = rec.payload or {}
        row = [
            str(rec.id),
            rec.external_id or "",
            rec.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        ] + [payload.get(f.field_name, "") for f in fields]
        writer.writerow([sanitize_csv_value(val) for val in row])

    output.seek(0)
    response = HttpResponse(output.getvalue(), content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="records_{schema.slug}.csv"'
    return response


def generate_jobs_csv_response(jobs_qs):
    """
    Generates a safe CSV file response for exported tenant jobs.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    headers = [
        "job_id",
        "file_name",
        "schema_name",
        "status",
        "total_rows",
        "successful_rows",
        "failed_rows",
        "duration_seconds",
        "created_at",
    ]
    writer.writerow([sanitize_csv_value(h) for h in headers])

    for j in jobs_qs[:1000]:
        row = [
            str(j.id),
            j.file_name,
            j.dataset_schema.name if j.dataset_schema else "",
            j.status,
            j.total_rows,
            j.successful_rows,
            j.failed_rows,
            j.duration_seconds or "",
            j.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        ]
        writer.writerow([sanitize_csv_value(val) for val in row])

    output.seek(0)
    response = HttpResponse(output.getvalue(), content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="ingestion_jobs.csv"'
    return response
