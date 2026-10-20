from django.urls import path

from .export_views import ExportJobsView, ExportRecordsView

app_name = "exports"

urlpatterns = [
    path("records/", ExportRecordsView.as_view(), name="export-records"),
    path("jobs/", ExportJobsView.as_view(), name="export-jobs"),
]
