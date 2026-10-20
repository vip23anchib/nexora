from rest_framework import serializers

from .models import AuditEvent


class AuditEventSerializer(serializers.ModelSerializer):
    actor_email = serializers.ReadOnlyField(source="actor.email")

    class Meta:
        model = AuditEvent
        fields = [
            "id",
            "actor",
            "actor_email",
            "action",
            "resource_type",
            "resource_id",
            "request_id",
            "metadata",
            "created_at",
        ]
        read_only_fields = fields
