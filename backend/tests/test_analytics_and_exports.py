import pytest
from apps.audit.models import AuditEvent
from apps.ingestion.models import ImportJob, ImportRowError
from apps.notifications.models import Notification
from apps.records.models import ImportedRecord
from apps.schemas.models import DatasetSchema
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken


@pytest.fixture
def analytics_data(authenticated_client):
    org = authenticated_client["organization"]
    user = authenticated_client["user"]

    schema = DatasetSchema.objects.create(
        organization=org,
        name="Analytics Test Schema",
        slug="analytics-test-schema",
        created_by=user,
    )
    from apps.schemas.models import DatasetField
    DatasetField.objects.create(
        dataset_schema=schema,
        field_name="code",
        display_name="Code",
        field_type="string",
        position=1,
    )
    DatasetField.objects.create(
        dataset_schema=schema,
        field_name="amount",
        display_name="Amount",
        field_type="string",
        position=2,
    )

    # Job 1: Completed (10 records)
    job1 = ImportJob.objects.create(
        organization=org,
        dataset_schema=schema,
        created_by=user,
        file_name="job1.csv",
        status=ImportJob.Status.COMPLETED,
        total_rows=10,
        processed_rows=10,
        successful_rows=10,
        failed_rows=0,
    )
    # Job 2: Completed with errors (5 success, 5 fail)
    job2 = ImportJob.objects.create(
        organization=org,
        dataset_schema=schema,
        created_by=user,
        file_name="job2.csv",
        status=ImportJob.Status.COMPLETED_WITH_ERRORS,
        total_rows=10,
        processed_rows=10,
        successful_rows=5,
        failed_rows=5,
    )

    # Row errors
    ImportRowError.objects.create(
        organization=org,
        import_job=job2,
        row_number=1,
        field_name="email",
        error_code="INVALID_EMAIL",
        error_message="Bad email",
    )
    ImportRowError.objects.create(
        organization=org,
        import_job=job2,
        row_number=2,
        field_name="age",
        error_code="NUMBER_TOO_LARGE",
        error_message="Too large",
    )

    # Record with formula injection attempt
    ImportedRecord.objects.create(
        organization=org,
        dataset_schema=schema,
        source_job=job1,
        external_id="=1+1",  # Formula injection attempt
        payload={"code": "@malicious", "amount": "+500"},
    )

    # Audit event
    AuditEvent.objects.create(
        organization=org,
        actor=user,
        action="TEST_ACTION",
        resource_type="DatasetSchema",
        resource_id=str(schema.id),
    )

    # Notification
    Notification.objects.create(
        organization=org,
        user=user,
        title="Welcome Notification",
        message="System alert",
        is_read=False,
    )

    return {"schema": schema, "job1": job1, "job2": job2}


@pytest.mark.django_db
def test_dashboard_analytics_kpis(authenticated_client, analytics_data):
    client = authenticated_client["client"]
    url = reverse("analytics:dashboard")

    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    data = response.data

    assert data["total_jobs"] == 2
    assert data["successful_jobs"] == 1
    assert data["partial_jobs"] == 1
    assert data["failed_jobs"] == 0
    assert data["total_records"] == 20
    assert data["successful_records"] == 15
    assert data["failed_records"] == 5
    assert data["validation_failure_rate"] == 25.0  # 5 / 20 * 100


@pytest.mark.django_db
def test_failure_distribution_analytics(authenticated_client, analytics_data):
    client = authenticated_client["client"]
    url = reverse("analytics:failure-distribution")

    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    codes = [item["error_code"] for item in response.data]
    assert "INVALID_EMAIL" in codes
    assert "NUMBER_TOO_LARGE" in codes


@pytest.mark.django_db
def test_audit_events_list_and_permissions(authenticated_client, analytics_data):
    client = authenticated_client["client"]
    url = reverse("audit:audit-events-list")

    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) >= 1
    assert response.data["results"][0]["action"] == "TEST_ACTION"


@pytest.mark.django_db
def test_notifications_lifecycle(authenticated_client, analytics_data):
    client = authenticated_client["client"]

    # Unread count
    count_url = reverse("notifications:notifications-unread-count")
    count_resp = client.get(count_url)
    assert count_resp.status_code == status.HTTP_200_OK
    assert count_resp.data["unread_count"] >= 1

    # Mark all read
    mark_all_url = reverse("notifications:notifications-mark-all-read")
    mark_resp = client.post(mark_all_url)
    assert mark_resp.status_code == status.HTTP_200_OK

    # Re-check count
    count_resp2 = client.get(count_url)
    assert count_resp2.data["unread_count"] == 0


@pytest.mark.django_db
def test_export_records_csv_and_formula_injection_defense(authenticated_client, analytics_data):
    client = authenticated_client["client"]
    schema = analytics_data["schema"]

    url = reverse("exports:export-records")
    response = client.get(f"{url}?schema_id={schema.id}")

    assert response.status_code == status.HTTP_200_OK
    assert response["Content-Type"] == "text/csv"
    csv_text = response.content.decode("utf-8")

    # Formula injection test: =1+1 should be prepended with '
    assert "'=1+1" in csv_text
    assert "'@malicious" in csv_text
    assert "'+500" in csv_text


@pytest.mark.django_db
def test_export_forbidden_for_viewer(
    api_client, user_factory, organization_factory, membership_factory, analytics_data
):
    org = analytics_data["schema"].organization
    viewer = user_factory(email="viewer.only@acme.io")
    membership_factory(organization=org, user=viewer, role="viewer")

    token = str(RefreshToken.for_user(viewer).access_token)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}", HTTP_X_ORGANIZATION_ID=str(org.id))

    url = reverse("exports:export-records")
    response = api_client.get(f"{url}?schema_id={analytics_data['schema'].id}")
    assert response.status_code == status.HTTP_403_FORBIDDEN
