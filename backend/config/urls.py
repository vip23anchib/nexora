from django.contrib import admin
from django.db import connection
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)


def health_live(request):
    """Liveness probe indicating process vitality."""
    return JsonResponse({"status": "live", "service": "nexora-backend"})


def health_ready(request):
    """Readiness probe verifying essential dependency connectivity."""
    db_ok = True
    db_error = None
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            row = cursor.fetchone()
            if not row or row[0] != 1:
                db_ok = False
    except Exception as e:
        db_ok = False
        db_error = str(e)

    status_code = 200 if db_ok else 503
    return JsonResponse(
        {
            "status": "ready" if db_ok else "unready",
            "database": "connected" if db_ok else "disconnected",
            "database_error": db_error,
        },
        status=status_code,
    )


urlpatterns = [
    path("admin/", admin.site.urls),
    # Health checks
    path("health/live/", health_live, name="health-live"),
    path("health/ready/", health_ready, name="health-ready"),
    # OpenAPI Documentation
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/v1/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/v1/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    # Authentication & Accounts
    path("api/v1/auth/", include("apps.accounts.urls")),
    # Organizations & Memberships
    path("api/v1/organization/", include("apps.organizations.urls")),
    # Schemas
    path("api/v1/schemas/", include("apps.schemas.urls")),
    # Data Sources
    path("api/v1/data-sources/", include("apps.datasources.urls")),
    # Ingestion Jobs
    path("api/v1/ingestion/", include("apps.ingestion.urls")),
    # Records Explorer
    path("api/v1/records/", include("apps.records.urls")),
]
