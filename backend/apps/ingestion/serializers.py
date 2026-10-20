from rest_framework import serializers

from .models import ImportJob, ImportRowError


class ImportRowErrorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImportRowError
        fields = [
            "id",
            "row_number",
            "field_name",
            "error_code",
            "error_message",
            "created_at",
        ]
        read_only_fields = fields


class ImportJobSerializer(serializers.ModelSerializer):
    schema_name = serializers.ReadOnlyField(source="dataset_schema.name")
    data_source_name = serializers.ReadOnlyField(source="data_source.name")
    created_by_email = serializers.ReadOnlyField(source="created_by.email")
    duration_seconds = serializers.ReadOnlyField()

    class Meta:
        model = ImportJob
        fields = [
            "id",
            "dataset_schema",
            "schema_name",
            "schema_version",
            "data_source",
            "data_source_name",
            "created_by",
            "created_by_email",
            "file_name",
            "file_size",
            "checksum",
            "idempotency_key",
            "status",
            "total_rows",
            "processed_rows",
            "successful_rows",
            "failed_rows",
            "started_at",
            "completed_at",
            "duration_seconds",
            "error_summary",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class CreateImportJobSerializer(serializers.Serializer):
    file = serializers.FileField(help_text="CSV file to upload and ingest.")
    dataset_schema_id = serializers.UUIDField(help_text="UUID of target DatasetSchema.")
    idempotency_key = serializers.CharField(max_length=128, required=False, allow_blank=True)
    data_source_id = serializers.UUIDField(required=False, allow_null=True)
