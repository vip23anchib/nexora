import uuid

from apps.common.models import TenantScopedModel
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class DatasetSchema(TenantScopedModel):
    """
    Defines the structural blueprint and typing constraints for datasets
    managed by an organization.
    """

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        DEPRECATED = "deprecated", "Deprecated"

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220)
    description = models.TextField(blank=True)
    version = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_schemas",
    )

    class Meta(TenantScopedModel.Meta):
        unique_together = [("organization", "slug", "version")]
        indexes = [
            models.Index(fields=["organization", "status"]),
            models.Index(fields=["organization", "slug"]),
        ]

    def __str__(self):
        return f"{self.name} (v{self.version}) [{self.organization.name}]"


class DatasetField(models.Model):
    """
    Defines an individual column or field constraint within a DatasetSchema.
    """

    class FieldType(models.TextChoices):
        STRING = "string", "String"
        INTEGER = "integer", "Integer"
        DECIMAL = "decimal", "Decimal"
        BOOLEAN = "boolean", "Boolean"
        DATE = "date", "Date"
        DATETIME = "datetime", "DateTime"
        EMAIL = "email", "Email"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dataset_schema = models.ForeignKey(
        DatasetSchema,
        on_delete=models.CASCADE,
        related_name="fields",
        db_index=True,
    )
    field_name = models.CharField(max_length=100)
    display_name = models.CharField(max_length=150)
    field_type = models.CharField(max_length=30, choices=FieldType.choices, default=FieldType.STRING)
    is_required = models.BooleanField(default=False)
    is_unique = models.BooleanField(default=False)
    default_value = models.CharField(max_length=255, blank=True, null=True)
    validation_rules = models.JSONField(
        default=dict,
        blank=True,
        help_text="Declarative validation constraints: min_length, max_length, min_value, max_value, regex, allowed_values",
    )
    position = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("dataset_schema", "field_name")]
        ordering = ["position", "created_at"]

    def __str__(self):
        return f"{self.field_name} ({self.field_type}) in {self.dataset_schema.name}"

    def clean(self):
        # Validate that validation_rules only contain safe supported keys
        allowed_keys = {"min_length", "max_length", "min_value", "max_value", "regex", "allowed_values"}
        if isinstance(self.validation_rules, dict):
            invalid_keys = set(self.validation_rules.keys()) - allowed_keys
            if invalid_keys:
                raise ValidationError(f"Invalid validation rule keys: {invalid_keys}")
        elif self.validation_rules:
            raise ValidationError("validation_rules must be a dictionary.")
