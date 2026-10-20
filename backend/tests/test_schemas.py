import pytest
from apps.ingestion.models import ImportJob
from apps.records.models import ImportedRecord
from apps.schemas.models import DatasetField, DatasetSchema
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken


@pytest.fixture
def candidate_schema(authenticated_client):
    org = authenticated_client["organization"]
    user = authenticated_client["user"]
    schema = DatasetSchema.objects.create(
        organization=org,
        name="Candidate Pipeline",
        slug="candidate-pipeline",
        version=1,
        created_by=user,
    )
    DatasetField.objects.create(
        dataset_schema=schema,
        field_name="candidate_id",
        display_name="Candidate ID",
        field_type=DatasetField.FieldType.STRING,
        is_required=True,
        is_unique=True,
        position=1,
    )
    DatasetField.objects.create(
        dataset_schema=schema,
        field_name="full_name",
        display_name="Full Name",
        field_type=DatasetField.FieldType.STRING,
        is_required=True,
        validation_rules={"min_length": 2, "max_length": 100},
        position=2,
    )
    DatasetField.objects.create(
        dataset_schema=schema,
        field_name="years_experience",
        display_name="Years Experience",
        field_type=DatasetField.FieldType.INTEGER,
        is_required=False,
        default_value="0",
        validation_rules={"min_value": 0, "max_value": 50},
        position=3,
    )
    DatasetField.objects.create(
        dataset_schema=schema,
        field_name="email",
        display_name="Email Address",
        field_type=DatasetField.FieldType.EMAIL,
        is_required=True,
        position=4,
    )
    return schema


@pytest.mark.django_db
def test_create_dataset_schema_with_fields(authenticated_client):
    client = authenticated_client["client"]
    url = reverse("schemas:schemas-list")

    payload = {
        "name": "Shipment Tracking",
        "slug": "shipment-tracking",
        "description": "Logistics tracking schema",
        "status": "active",
        "fields": [
            {
                "field_name": "tracking_number",
                "display_name": "Tracking Number",
                "field_type": "string",
                "is_required": True,
                "is_unique": True,
                "position": 1,
            },
            {
                "field_name": "weight_kg",
                "display_name": "Weight (KG)",
                "field_type": "decimal",
                "is_required": True,
                "validation_rules": {"min_value": 0.1, "max_value": 1000.0},
                "position": 2,
            },
        ],
    }

    response = client.post(url, payload, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["name"] == "Shipment Tracking"
    assert len(response.data["fields"]) == 2
    assert response.data["fields"][0]["field_name"] == "tracking_number"


@pytest.mark.django_db
def test_validate_sample_payload(authenticated_client, candidate_schema):
    client = authenticated_client["client"]
    url = reverse("schemas:schemas-validate-sample", kwargs={"pk": candidate_schema.id})

    payload = {
        "sample_rows": [
            {
                "candidate_id": "CAND-001",
                "full_name": "Alice Smith",
                "years_experience": "5",
                "email": "alice@example.com",
            },
            {
                "candidate_id": "CAND-002",
                "full_name": "B",  # too short (< 2)
                "years_experience": "-2",  # too small (< 0)
                "email": "not-an-email",  # invalid email
            },
        ]
    }

    response = client.post(url, payload, format="json")
    assert response.status_code == status.HTTP_200_OK
    data = response.data
    assert data["total_rows"] == 2
    assert data["valid_count"] == 1
    assert data["error_count"] >= 3
    assert data["is_valid"] is False


@pytest.mark.django_db
def test_schema_cross_tenant_isolation(
    api_client, user_factory, organization_factory, membership_factory, candidate_schema
):
    # Org B user
    user_b = user_factory(email="intruder@beta.io")
    org_b = organization_factory(name="Org Beta", slug="org-beta")
    membership_factory(organization=org_b, user=user_b, role="org_admin")

    token_b = str(RefreshToken.for_user(user_b).access_token)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_b}", HTTP_X_ORGANIZATION_ID=str(org_b.id))

    url = reverse("schemas:schemas-detail", kwargs={"pk": candidate_schema.id})
    response = api_client.get(url)

    # Must return 404 to avoid leaking existence of schemas in other organizations
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_data_source_lifecycle_and_deactivate(authenticated_client):
    client = authenticated_client["client"]
    url = reverse("datasources:data-sources-list")

    create_data = {
        "name": "Warehouse S3 Inbound",
        "source_type": "file_upload",
        "description": "Daily candidate uploads",
        "configuration": {"bucket": "candidate-uploads"},
    }
    response = client.post(url, create_data, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    source_id = response.data["id"]
    assert response.data["is_active"] is True

    # Deactivate action
    deactivate_url = reverse("datasources:data-sources-deactivate", kwargs={"pk": source_id})
    deactivate_resp = client.post(deactivate_url)
    assert deactivate_resp.status_code == status.HTTP_200_OK
    assert deactivate_resp.data["is_active"] is False


@pytest.mark.django_db
def test_records_explorer_list_and_filter(authenticated_client, candidate_schema):
    client = authenticated_client["client"]
    org = authenticated_client["organization"]
    user = authenticated_client["user"]

    job = ImportJob.objects.create(
        organization=org,
        dataset_schema=candidate_schema,
        created_by=user,
        file_name="candidates.csv",
        checksum="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        status=ImportJob.Status.COMPLETED,
    )

    ImportedRecord.objects.create(
        organization=org,
        dataset_schema=candidate_schema,
        source_job=job,
        source_row_number=1,
        external_id="CAND-100",
        payload={"candidate_id": "CAND-100", "full_name": "Carol Danvers", "email": "carol@marvel.com"},
    )

    url = reverse("records:records-list")
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["external_id"] == "CAND-100"
    assert response.data["results"][0]["schema_name"] == candidate_schema.name
