import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

User = get_user_model()


@pytest.mark.django_db
def test_create_user(user_factory):
    user = user_factory(email="developer@nexora.io", first_name="Dev", last_name="User")
    assert user.email == "developer@nexora.io"
    assert user.full_name == "Dev User"
    assert user.is_active is True
    assert user.is_platform_admin is False
    assert user.check_password("password123") is True


@pytest.mark.django_db
def test_user_login_success(api_client, user_factory, organization_factory, membership_factory):
    user = user_factory(email="operator@nexora.io", password="securepassword123")
    org = organization_factory(name="Acme Logistics", slug="acme-logistics")
    membership_factory(organization=org, user=user, role="operator")

    url = reverse("accounts:login")
    response = api_client.post(
        url,
        {"email": "operator@nexora.io", "password": "securepassword123"},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data
    assert "refresh" in response.data
    assert response.data["user"]["email"] == "operator@nexora.io"
    assert response.data["active_organization"]["name"] == "Acme Logistics"
    assert response.data["active_role"] == "operator"


@pytest.mark.django_db
def test_user_login_invalid_credentials(api_client, user_factory):
    user_factory(email="analyst@nexora.io", password="validpassword")
    url = reverse("accounts:login")
    response = api_client.post(url, {"email": "analyst@nexora.io", "password": "wrongpassword"}, format="json")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_me_endpoint_authenticated(authenticated_client):
    client = authenticated_client["client"]
    url = reverse("accounts:me")
    response = client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["user"]["email"] == "admin@alpha.io"
    assert response.data["active_organization"]["slug"] == "org-alpha"
    assert response.data["active_role"] == "org_admin"


@pytest.mark.django_db
def test_me_endpoint_unauthenticated(api_client):
    url = reverse("accounts:me")
    response = api_client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
