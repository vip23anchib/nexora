import pytest
from apps.organizations.models import Organization, OrganizationMembership
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user_factory(db):
    def create_user(email="user@nexora.io", password="password123", **kwargs):
        return User.objects.create_user(email=email, password=password, **kwargs)

    return create_user


@pytest.fixture
def organization_factory(db):
    def create_org(name="Acme Corp", slug="acme-corp", **kwargs):
        return Organization.objects.create(name=name, slug=slug, **kwargs)

    return create_org


@pytest.fixture
def membership_factory(db):
    def create_membership(organization, user, role="org_admin", **kwargs):
        return OrganizationMembership.objects.create(
            organization=organization, user=user, role=role, **kwargs
        )

    return create_membership


@pytest.fixture
def authenticated_client(
    api_client, user_factory, organization_factory, membership_factory
):
    """Provides an APIClient authenticated as an Org Admin of Org Alpha."""
    user = user_factory(email="admin@alpha.io", first_name="Alpha", last_name="Admin")
    org = organization_factory(name="Org Alpha", slug="org-alpha")
    membership = membership_factory(organization=org, user=user, role="org_admin")

    token = str(RefreshToken.for_user(user).access_token)
    api_client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {token}",
        HTTP_X_ORGANIZATION_ID=str(org.id),
    )
    return {
        "client": api_client,
        "user": user,
        "organization": org,
        "membership": membership,
        "token": token,
    }
