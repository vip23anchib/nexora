from apps.common.permissions import IsTenantMember
from apps.common.views import TenantContextMixin
from apps.datasources.models import DataSource
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from .models import ImportJob, ImportRowError
from .serializers import (
    CreateImportJobSerializer,
    ImportJobSerializer,
    ImportRowErrorSerializer,
)
from .services import create_import_job, process_import_job, retry_import_job


class ImportJobViewSet(TenantContextMixin, viewsets.ReadOnlyModelViewSet):
    """
    Manage CSV dataset uploads, view processing progress, inspect row-level errors,
    and trigger safe idempotent retries.
    """

    serializer_class = ImportJobSerializer
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filterset_fields = ["status", "dataset_schema", "data_source"]
    search_fields = ["file_name", "checksum", "idempotency_key"]
    ordering_fields = ["created_at", "total_rows", "processed_rows", "failed_rows"]

    def get_queryset(self):
        tenant = getattr(self.request, "tenant", None)
        if not tenant:
            return ImportJob.objects.none()
        return (
            ImportJob.objects.filter(organization=tenant)
            .select_related("dataset_schema", "data_source", "created_by")
            .order_by("-created_at")
        )

    @extend_schema(
        summary="Upload CSV and initiate import job",
        request=CreateImportJobSerializer,
        responses={201: ImportJobSerializer},
    )
    def create(self, request, *args, **kwargs):
        if not (request.membership and request.membership.role in ["org_admin", "operator"]):
            return Response(
                {"detail": "Only organization administrators and operators can submit import jobs."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = CreateImportJobSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        file_obj = serializer.validated_data["file"]
        schema_id = serializer.validated_data["dataset_schema_id"]
        idempotency_key = serializer.validated_data.get("idempotency_key")
        data_source_id = serializer.validated_data.get("data_source_id")

        data_source = None
        if data_source_id:
            data_source = DataSource.objects.filter(
                organization=request.tenant,
                id=data_source_id,
            ).first()

        job, created = create_import_job(
            organization=request.tenant,
            user=request.user,
            schema_id=schema_id,
            file_obj=file_obj,
            idempotency_key=idempotency_key,
            data_source=data_source,
        )

        # Process job (synchronous execution or dispatched to Celery background task)
        # Check if Celery task is configured or run synchronously
        try:
            from .tasks import run_import_job_task

            run_import_job_task.delay(str(job.id))
        except Exception:
            process_import_job(job.id)

        job.refresh_from_db()
        return Response(
            ImportJobSerializer(job).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @extend_schema(
        summary="List row-level validation errors for a specific job",
        responses={200: ImportRowErrorSerializer(many=True)},
    )
    @action(detail=True, methods=["get"], url_path="errors")
    def errors(self, request, pk=None):
        job = self.get_object()
        errors = ImportRowError.objects.filter(import_job=job).order_by("row_number")
        page = self.paginate_queryset(errors)
        if page is not None:
            serializer = ImportRowErrorSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = ImportRowErrorSerializer(errors, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Retry failed or partially completed import job",
        responses={200: ImportJobSerializer},
    )
    @action(detail=True, methods=["post"], url_path="retry")
    def retry(self, request, pk=None):
        if not (request.membership and request.membership.role in ["org_admin", "operator"]):
            return Response(
                {"detail": "Only organization administrators and operators can retry import jobs."},
                status=status.HTTP_403_FORBIDDEN,
            )
        job = self.get_object()
        updated_job = retry_import_job(job.id, request.user)
        return Response(ImportJobSerializer(updated_job).data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Cancel queued or active import job",
        responses={200: ImportJobSerializer},
    )
    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        if not (request.membership and request.membership.role in ["org_admin", "operator"]):
            return Response(
                {"detail": "Only organization administrators and operators can cancel import jobs."},
                status=status.HTTP_403_FORBIDDEN,
            )
        job = self.get_object()
        if job.status in [ImportJob.Status.COMPLETED, ImportJob.Status.FAILED, ImportJob.Status.CANCELLED]:
            return Response(
                {"detail": f"Job in state '{job.status}' cannot be cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        job.status = ImportJob.Status.CANCELLED
        job.save(update_fields=["status", "updated_at"])
        return Response(ImportJobSerializer(job).data, status=status.HTTP_200_OK)
