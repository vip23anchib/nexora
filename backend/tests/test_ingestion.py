import pytest
from apps.ingestion.models import ImportJob
from apps.records.models import ImportedRecord
from apps.schemas.models import DatasetField, DatasetSchema
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken


@pytest.fixture
def shipment_schema(authenticated_client):
    org = authenticated_client["organization"]
    user = authenticated_client["user"]
    schema = DatasetSchema.objects.create(
        organization=org,
        name="Logistics Shipments",
        slug="logistics-shipments",
        version=1,
        created_by=user,
    )
    DatasetField.objects.create(
        dataset_schema=schema,
        field_name="tracking_id",
        display_name="Tracking ID",
        field_type="string",
        is_required=True,
        position=1,
    )
    DatasetField.objects.create(
        dataset_schema=schema,
        field_name="origin",
        display_name="Origin City",
        field_type="string",
        is_required=True,
        position=2,
    )
    DatasetField.objects.create(
        dataset_schema=schema,
        field_name="destination",
        display_name="Destination City",
        field_type="string",
        is_required=True,
        position=3,
    )
    DatasetField.objects.create(
        dataset_schema=schema,
        field_name="weight",
        display_name="Weight (kg)",
        field_type="decimal",
        is_required=True,
        validation_rules={"min_value": 0.5, "max_value": 500.0},
        position=4,
    )
    return schema


@pytest.mark.django_db
def test_valid_csv_ingestion_lifecycle(authenticated_client, shipment_schema):
    client = authenticated_client["client"]
    url = reverse("ingestion:import-jobs-list")

    csv_content = (
        "tracking_id,origin,destination,weight\n"
        "TRK-1001,Seattle,Chicago,12.5\n"
        "TRK-1002,Denver,Boston,45.0\n"
        "TRK-1003,Austin,Miami,8.2\n"
    ).encode("utf-8")

    uploaded_file = SimpleUploadedFile("shipments.csv", csv_content, content_type="text/csv")

    response = client.post(
        url,
        {
            "file": uploaded_file,
            "dataset_schema_id": str(shipment_schema.id),
            "idempotency_key": "shipment-batch-001",
        },
        format="multipart",
    )

    assert response.status_code == status.HTTP_201_CREATED
    job_id = response.data["id"]
    assert response.data["status"] == ImportJob.Status.COMPLETED
    assert response.data["total_rows"] == 3
    assert response.data["successful_rows"] == 3
    assert response.data["failed_rows"] == 0

    # Verify records in database
    records = ImportedRecord.objects.filter(source_job_id=job_id)
    assert records.count() == 3


@pytest.mark.django_db
def test_csv_ingestion_with_row_errors(authenticated_client, shipment_schema):
    client = authenticated_client["client"]
    url = reverse("ingestion:import-jobs-list")

    csv_content = (
        "tracking_id,origin,destination,weight\n"
        "TRK-2001,Seattle,Chicago,15.0\n"
        "TRK-2002,Denver,Boston,999.0\n"  # weight > 500 max_value
        "TRK-2003,Austin,Miami,invalid_weight\n"  # decimal parse error
    ).encode("utf-8")

    uploaded_file = SimpleUploadedFile("partial.csv", csv_content, content_type="text/csv")

    response = client.post(
        url,
        {
            "file": uploaded_file,
            "dataset_schema_id": str(shipment_schema.id),
        },
        format="multipart",
    )

    assert response.status_code == status.HTTP_201_CREATED
    job_id = response.data["id"]
    assert response.data["status"] == ImportJob.Status.COMPLETED_WITH_ERRORS
    assert response.data["successful_rows"] == 1
    assert response.data["failed_rows"] == 2

    # Verify row errors endpoint
    errors_url = reverse("ingestion:import-jobs-errors", kwargs={"pk": job_id})
    err_resp = client.get(errors_url)
    assert err_resp.status_code == status.HTTP_200_OK
    assert len(err_resp.data["results"]) == 2
    row_numbers = [e["row_number"] for e in err_resp.data["results"]]
    assert 2 in row_numbers
    assert 3 in row_numbers


@pytest.mark.django_db
def test_csv_ingestion_missing_required_column(authenticated_client, shipment_schema):
    client = authenticated_client["client"]
    url = reverse("ingestion:import-jobs-list")

    # Missing "destination" column entirely
    csv_content = ("tracking_id,origin,weight\nTRK-3001,Seattle,15.0\n").encode("utf-8")

    uploaded_file = SimpleUploadedFile("bad_headers.csv", csv_content, content_type="text/csv")

    response = client.post(
        url,
        {
            "file": uploaded_file,
            "dataset_schema_id": str(shipment_schema.id),
        },
        format="multipart",
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["status"] == ImportJob.Status.FAILED
    assert "Missing required CSV columns" in response.data["error_summary"]


@pytest.mark.django_db
def test_idempotent_duplicate_upload(authenticated_client, shipment_schema):
    client = authenticated_client["client"]
    url = reverse("ingestion:import-jobs-list")

    csv_content = ("tracking_id,origin,destination,weight\nTRK-4001,Dallas,Atlanta,20.0\n").encode("utf-8")

    file1 = SimpleUploadedFile("upload1.csv", csv_content, content_type="text/csv")
    resp1 = client.post(
        url,
        {"file": file1, "dataset_schema_id": str(shipment_schema.id), "idempotency_key": "key-xyz-123"},
        format="multipart",
    )
    assert resp1.status_code == status.HTTP_201_CREATED
    first_job_id = resp1.data["id"]

    # Re-upload with same idempotency key
    file2 = SimpleUploadedFile("upload2.csv", csv_content, content_type="text/csv")
    resp2 = client.post(
        url,
        {"file": file2, "dataset_schema_id": str(shipment_schema.id), "idempotency_key": "key-xyz-123"},
        format="multipart",
    )
    assert resp2.status_code == status.HTTP_200_OK
    assert resp2.data["id"] == first_job_id

    # Verify records were NOT duplicated
    assert ImportedRecord.objects.filter(dataset_schema=shipment_schema).count() == 1


@pytest.mark.django_db
def test_retry_import_job_is_idempotent(authenticated_client, shipment_schema):
    client = authenticated_client["client"]
    url = reverse("ingestion:import-jobs-list")

    csv_content = (
        "tracking_id,origin,destination,weight\n"
        "TRK-5001,Portland,Phoenix,25.0\n"
        "TRK-5002,Orlando,Tampa,-5.0\n"  # invalid weight
    ).encode("utf-8")

    file_obj = SimpleUploadedFile("retry_test.csv", csv_content, content_type="text/csv")
    resp = client.post(
        url,
        {"file": file_obj, "dataset_schema_id": str(shipment_schema.id)},
        format="multipart",
    )
    assert resp.status_code == status.HTTP_201_CREATED
    job_id = resp.data["id"]
    assert resp.data["status"] == ImportJob.Status.COMPLETED_WITH_ERRORS

    # Trigger retry
    retry_url = reverse("ingestion:import-jobs-retry", kwargs={"pk": job_id})
    retry_resp = client.post(retry_url)
    assert retry_resp.status_code == status.HTTP_200_OK

    # Ensure already-committed record TRK-5001 was not duplicated
    records = ImportedRecord.objects.filter(dataset_schema=shipment_schema)
    assert records.count() == 1


@pytest.mark.django_db
def test_ingestion_cross_tenant_isolation(
    api_client, user_factory, organization_factory, membership_factory, shipment_schema
):
    # Org A job
    org_a = shipment_schema.organization
    job = ImportJob.objects.create(
        organization=org_a,
        dataset_schema=shipment_schema,
        file_name="confidential_a.csv",
        checksum="1111111111111111111111111111111111111111111111111111111111111111",
        status=ImportJob.Status.COMPLETED,
    )

    # Org B user
    user_b = user_factory(email="agent@beta.io")
    org_b = organization_factory(name="Org Beta", slug="org-beta-ingest")
    membership_factory(organization=org_b, user=user_b, role="org_admin")

    token_b = str(RefreshToken.for_user(user_b).access_token)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_b}", HTTP_X_ORGANIZATION_ID=str(org_b.id))

    # Access Org A's job details
    url = reverse("ingestion:import-jobs-detail", kwargs={"pk": job.id})
    response = api_client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # Attempt to retry Org A's job
    retry_url = reverse("ingestion:import-jobs-retry", kwargs={"pk": job.id})
    retry_resp = api_client.post(retry_url)
    assert retry_resp.status_code == status.HTTP_404_NOT_FOUND
