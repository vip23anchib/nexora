from rest_framework import serializers

from .models import WorkflowEvent


class WorkflowEventSerializer(serializers.ModelSerializer):
    file_name = serializers.ReadOnlyField(source="import_job.file_name")

    class Meta:
        model = WorkflowEvent
        fields = [
            "id",
            "import_job",
            "file_name",
            "event_type",
            "previous_state",
            "new_state",
            "metadata",
            "created_at",
        ]
        read_only_fields = fields
