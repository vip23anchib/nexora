import pytest
from apps.ingestion.models import ImportJob
from apps.schemas.models import DatasetSchema
from apps.workflows.models import WorkflowEvent
from apps.workflows.services import transition_job_state
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken


@pytest.fixture
def workflow_job(authenticated_client):
    org = authenticated_client["organization"]
    user = authenticated_client["user"]
    schema = DatasetSchema.objects.create(
        organization=org,
        name="Appointment Workflow",
        slug="appointment-workflow",
        created_by=user,
    )
    job = ImportJob.objects.create(
        organization=org,
        dataset_schema=schema,
        created_by=user,
        file_name="appointments.csv",
        checksum="aaaa1111222233334444555566667777888899990000aaaa1111222233334444",
        status=ImportJob.Status.QUEUED,
    )
    return job


@pytest.mark.django_db
def test_valid_state_transitions_and_events(workflow_job):
    # Transition: QUEUED -> PROCESSING
    job, ev1 = transition_job_state(
        workflow_job.id,
        ImportJob.Status.PROCESSING,
        event_type="WORKER_PICKED_UP",
        metadata={"worker_id": "worker-1"},
    )
    assert job.status == ImportJob.Status.PROCESSING
    assert job.started_at is not None
    assert ev1.previous_state == ImportJob.Status.QUEUED
    assert ev1.new_state == ImportJob.Status.PROCESSING
    assert ev1.event_type == "WORKER_PICKED_UP"

    # Transition: PROCESSING -> COMPLETED
    job, ev2 = transition_job_state(
        workflow_job.id,
        ImportJob.Status.COMPLETED,
        event_type="INGESTION_SUCCEEDED",
        metadata={"rows": 100},
    )
    assert job.status == ImportJob.Status.COMPLETED
    assert job.completed_at is not None
    assert ev2.previous_state == ImportJob.Status.PROCESSING
    assert ev2.new_state == ImportJob.Status.COMPLETED

    # Total events created
    assert WorkflowEvent.objects.filter(import_job=workflow_job).count() == 2


@pytest.mark.django_db
def test_invalid_state_transition_rejection(workflow_job):
    # Attempting QUEUED -> COMPLETED directly (bypassing PROCESSING)
    with pytest.raises(ValidationError) as exc_info:
        transition_job_state(workflow_job.id, ImportJob.Status.COMPLETED)
    assert "Invalid workflow state transition" in str(exc_info.value)

    # Move to COMPLETED properly
    transition_job_state(workflow_job.id, ImportJob.Status.PROCESSING)
    transition_job_state(workflow_job.id, ImportJob.Status.COMPLETED)

    # Attempting to move terminal COMPLETED -> PROCESSING
    with pytest.raises(ValidationError) as exc_info2:
        transition_job_state(workflow_job.id, ImportJob.Status.PROCESSING)
    assert "Invalid workflow state transition" in str(exc_info2.value)


@pytest.mark.django_db
def test_workflow_events_api_and_isolation(
    authenticated_client, workflow_job, api_client, user_factory, organization_factory, membership_factory
):
    client = authenticated_client["client"]

    # Generate an event
    transition_job_state(workflow_job.id, ImportJob.Status.PROCESSING)
    transition_job_state(workflow_job.id, ImportJob.Status.COMPLETED)

    url = reverse("workflows:workflow-events-list")
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 2
    assert str(response.data["results"][0]["import_job"]) == str(workflow_job.id)

    # Cross-tenant isolation
    user_b = user_factory(email="outsider@beta.io")
    org_b = organization_factory(name="Org Beta", slug="org-beta-wf")
    membership_factory(organization=org_b, user=user_b, role="org_admin")

    token_b = str(RefreshToken.for_user(user_b).access_token)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_b}", HTTP_X_ORGANIZATION_ID=str(org_b.id))

    response_b = api_client.get(url)
    assert response_b.status_code == status.HTTP_200_OK
    # Must be empty for Org Beta
    assert len(response_b.data["results"]) == 0
