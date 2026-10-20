from django.urls import path

from .views import (
    DashboardAnalyticsView,
    FailureDistributionView,
    IngestionTrendsView,
    ProcessingPerformanceView,
    SchemaUsageView,
)

app_name = "analytics"

urlpatterns = [
    path("dashboard/", DashboardAnalyticsView.as_view(), name="dashboard"),
    path("ingestion-trends/", IngestionTrendsView.as_view(), name="ingestion-trends"),
    path("failure-distribution/", FailureDistributionView.as_view(), name="failure-distribution"),
    path("processing-performance/", ProcessingPerformanceView.as_view(), name="processing-performance"),
    path("schema-usage/", SchemaUsageView.as_view(), name="schema-usage"),
]
