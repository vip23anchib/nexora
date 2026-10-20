from apps.ingestion.models import ImportJob
from apps.records.models import ImportedRecord
from apps.schemas.models import DatasetSchema
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status, views
from rest_framework.response import Response

from .exports import generate_jobs_csv_response, generate_records_csv_response
from .permissions import IsTenantMember
from .views import TenantContextMixin


class ExportRecordsView(TenantContextMixin, views.APIView):
    """
    Exports tenant records in CSV format with formula injection sanitization.
    Restricted to Analysts, Operators, and Admins.
    """

    permission_classes = [permissions.IsAuthenticated, IsTenantMember]

    @extend_schema(summary="Export records as sanitized CSV")
    def get(self, request):
        if request.membership and request.membership.role == "viewer":
            return Response(
                {"detail": "Viewers do not have permission to export records."},
                status=status.HTTP_403_FORBIDDEN,
            )

        schema_id = request.query_params.get("schema_id")
        if not schema_id:
            return Response({"error": "Query param 'schema_id' is required."}, status=status.HTTP_400_BAD_REQUEST)

        schema = DatasetSchema.objects.filter(organization=request.tenant, id=schema_id).first()
        if not schema:
            return Response({"error": "Schema not found."}, status=status.HTTP_404_NOT_FOUND)

        records_qs = ImportedRecord.objects.filter(organization=request.tenant, dataset_schema=schema).order_by(
            "-created_at"
        )
        return generate_records_csv_response(records_qs, schema)


class ExportJobsView(TenantContextMixin, views.APIView):
    """
    Exports ingestion job execution logs in sanitized CSV format.
    """

    permission_classes = [permissions.IsAuthenticated, IsTenantMember]

    @extend_schema(summary="Export jobs as sanitized CSV")
    def get(self, request):
        if request.membership and request.membership.role == "viewer":
            return Response(
                {"detail": "Viewers do not have permission to export jobs."},
                status=status.HTTP_403_FORBIDDEN,
            )

        jobs_qs = (
            ImportJob.objects.filter(organization=request.tenant)
            .select_related("dataset_schema")
            .order_by("-created_at")
        )
        return generate_jobs_csv_response(jobs_qs)
