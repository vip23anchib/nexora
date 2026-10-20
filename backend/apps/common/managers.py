from django.db import models


class TenantScopedQuerySet(models.QuerySet):
    """QuerySet that enforces filtering by tenant/organization."""

    def for_tenant(self, tenant):
        if not tenant:
            return self.none()
        tenant_id = getattr(tenant, "id", tenant)
        return self.filter(organization_id=tenant_id)


class TenantScopedManager(models.Manager):
    """Manager providing automatic tenant filtering capabilities."""

    def get_queryset(self):
        return TenantScopedQuerySet(self.model, using=self._db)

    def for_tenant(self, tenant):
        return self.get_queryset().for_tenant(tenant)
