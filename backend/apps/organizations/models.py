import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Organization(models.Model):
    """Represents a customer tenant organization in Nexora."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, db_index=True)
    description = models.TextField(blank=True)
    timezone = models.CharField(max_length=50, default="UTC")
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["is_active", "created_at"]),
        ]

    def __str__(self):
        return self.name


class OrganizationMembership(models.Model):
    """Represents a user's membership and assigned RBAC role within an organization."""

    class Role(models.TextChoices):
        ORG_ADMIN = "org_admin", "Organization Administrator"
        OPERATOR = "operator", "Operator"
        ANALYST = "analyst", "Analyst"
        VIEWER = "viewer", "Viewer"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="memberships",
        db_index=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="memberships",
        db_index=True,
    )
    role = models.CharField(
        max_length=30,
        choices=Role.choices,
        default=Role.VIEWER,
        db_index=True,
    )
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("organization", "user")]
        ordering = ["joined_at"]
        indexes = [
            models.Index(fields=["organization", "role"]),
            models.Index(fields=["user", "is_active"]),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.organization.name} ({self.role})"

    def clean(self):
        # Prevent demoting or deactivating the last active org_admin
        if self.pk:
            original = OrganizationMembership.objects.filter(pk=self.pk).first()
            if (
                original
                and original.role == self.Role.ORG_ADMIN
                and (self.role != self.Role.ORG_ADMIN or not self.is_active)
            ):
                remaining_admins = (
                    OrganizationMembership.objects.filter(
                        organization=self.organization,
                        role=self.Role.ORG_ADMIN,
                        is_active=True,
                    )
                    .exclude(pk=self.pk)
                    .count()
                )
                if remaining_admins == 0:
                    raise ValidationError(
                        "Cannot demote or deactivate the last administrator of the organization."
                    )
