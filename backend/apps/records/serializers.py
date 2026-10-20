from rest_framework import serializers

from .models import ImportedRecord


class ImportedRecordSerializer(serializers.ModelSerializer):
    schema_name = serializers.ReadOnlyField(source="dataset_schema.name")
    source_file_name = serializers.ReadOnlyField(source="source_job.file_name")

    class Meta:
        model = ImportedRecord
        fields = [
            "id",
            "dataset_schema",
            "schema_name",
            "source_job",
            "source_file_name",
            "source_row_number",
            "external_id",
            "payload",
            "record_hash",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
