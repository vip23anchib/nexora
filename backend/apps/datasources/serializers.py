from rest_framework import serializers

from .models import DataSource


class DataSourceSerializer(serializers.ModelSerializer):
    created_by_email = serializers.ReadOnlyField(source="created_by.email")

    class Meta:
        model = DataSource
        fields = [
            "id",
            "name",
            "source_type",
            "description",
            "configuration",
            "is_active",
            "created_by",
            "created_by_email",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]

    def create(self, validated_data):
        organization = self.context["organization"]
        user = self.context.get("user")
        return DataSource.objects.create(
            organization=organization,
            created_by=user,
            **validated_data,
        )
