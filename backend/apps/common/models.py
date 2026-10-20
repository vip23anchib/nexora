import uuid

from django.db import models

from .managers import TenantScopedManager


class BaseModel(models.Model):
    """Abstract base model with UUID primary key and UTC timestamps."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]


class TenantScopedModel(BaseModel):
    """Abstract model for tenant-isolated entities."""

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)ss",
        db_index=True,
    )

    objects = TenantScopedManager()

    class Meta:
        abstract = True
        ordering = ["-created_at"]
