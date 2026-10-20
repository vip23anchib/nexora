from django.db import transaction
from rest_framework import serializers

from .models import DatasetField, DatasetSchema
from .validators import validate_row_against_schema


class DatasetFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatasetField
        fields = [
            "id",
            "field_name",
            "display_name",
            "field_type",
            "is_required",
            "is_unique",
            "default_value",
            "validation_rules",
            "position",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_field_name(self, value):
        cleaned = value.strip().lower()
        if not cleaned.isidentifier():
            raise serializers.ValidationError(
                "field_name must be a valid alphanumeric identifier (e.g., 'patient_id', 'amount')."
            )
        return cleaned


class DatasetSchemaSerializer(serializers.ModelSerializer):
    fields = DatasetFieldSerializer(many=True, required=False)
    created_by_email = serializers.ReadOnlyField(source="created_by.email")
    records_count = serializers.SerializerMethodField()

    class Meta:
        model = DatasetSchema
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "version",
            "status",
            "created_by",
            "created_by_email",
            "fields",
            "records_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "version", "created_by", "created_at", "updated_at"]

    def get_records_count(self, obj):
        return getattr(obj, "records_count", obj.records.count() if hasattr(obj, "records") else 0)

    @transaction.atomic
    def create(self, validated_data):
        fields_data = validated_data.pop("fields", [])
        organization = self.context["organization"]
        user = self.context.get("user")

        schema = DatasetSchema.objects.create(
            organization=organization,
            created_by=user,
            **validated_data,
        )

        for pos, field_data in enumerate(fields_data):
            field_data.setdefault("position", pos)
            DatasetField.objects.create(
                dataset_schema=schema,
                **field_data,
            )

        return schema

    @transaction.atomic
    def update(self, instance, validated_data):
        fields_data = validated_data.pop("fields", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if fields_data is not None:
            # Replace or update fields
            instance.fields.all().delete()
            for pos, field_data in enumerate(fields_data):
                field_data.setdefault("position", pos)
                DatasetField.objects.create(
                    dataset_schema=instance,
                    **field_data,
                )

        return instance


class ValidateSampleSerializer(serializers.Serializer):
    sample_rows = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=False,
        max_length=50,
        help_text="Array of sample row dictionaries to test against this schema's validation rules.",
    )

    def validate_sample(self, schema):
        rows = self.validated_data["sample_rows"]
        fields = list(schema.fields.all())
        valid_rows = []
        errors = []

        for idx, row in enumerate(rows, start=1):
            cleaned, row_errors = validate_row_against_schema(fields, row, row_number=idx)
            if row_errors:
                errors.extend([err.to_dict() for err in row_errors])
            else:
                valid_rows.append({"row_number": idx, "payload": cleaned})

        return {
            "total_rows": len(rows),
            "valid_count": len(valid_rows),
            "error_count": len(errors),
            "is_valid": len(errors) == 0,
            "errors": errors,
            "sample_valid_rows": valid_rows[:5],
        }
