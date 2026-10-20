from apps.common.permissions import IsTenantMember
from apps.common.views import TenantContextMixin
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, views
from rest_framework.response import Response

from .services import (
    get_dashboard_analytics,
    get_failure_distribution,
    get_ingestion_trends,
    get_processing_performance,
    get_schema_usage,
)


class DashboardAnalyticsView(TenantContextMixin, views.APIView):
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]

    @extend_schema(summary="Get operational dashboard metrics")
    def get(self, request):
        data = get_dashboard_analytics(request.tenant)
        return Response(data)


class IngestionTrendsView(TenantContextMixin, views.APIView):
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]

    @extend_schema(summary="Get daily ingestion throughput and error trends")
    def get(self, request):
        days = int(request.query_params.get("days", 7))
        data = get_ingestion_trends(request.tenant, days=min(days, 30))
        return Response(data)


class FailureDistributionView(TenantContextMixin, views.APIView):
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]

    @extend_schema(summary="Get distribution of row validation errors")
    def get(self, request):
        data = get_failure_distribution(request.tenant)
        return Response(data)


class ProcessingPerformanceView(TenantContextMixin, views.APIView):
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]

    @extend_schema(summary="Get latency and duration percentiles for completed ingestion jobs")
    def get(self, request):
        data = get_processing_performance(request.tenant)
        return Response(data)


class SchemaUsageView(TenantContextMixin, views.APIView):
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]

    @extend_schema(summary="Get dataset schema utilization and ingestion volume")
    def get(self, request):
        data = get_schema_usage(request.tenant)
        return Response(data)
