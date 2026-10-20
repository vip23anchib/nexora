import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken


@pytest.mark.django_db
def test_get_organization_detail(authenticated_client):
    client = authenticated_client["client"]
    org = authenticated_client["organization"]

    url = reverse("organizations:organization-detail")
    response = client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == str(org.id)
    assert response.data["name"] == org.name
    assert response.data["slug"] == org.slug


@pytest.mark.django_db
def test_update_organization_settings_by_admin(authenticated_client):
    client = authenticated_client["client"]
    url = reverse("organizations:organization-detail")
    response = client.patch(
        url,
        {"description": "Updated corporate profile", "timezone": "America/New_York"},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["description"] == "Updated corporate profile"
    assert response.data["timezone"] == "America/New_York"


@pytest.mark.django_db
def test_update_organization_settings_forbidden_for_viewer(
    api_client, user_factory, organization_factory, membership_factory
):
    user = user_factory(email="viewer@alpha.io")
    org = organization_factory(name="Alpha Org", slug="alpha-org")
    membership_factory(organization=org, user=user, role="viewer")

    token = str(RefreshToken.for_user(user).access_token)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}", HTTP_X_ORGANIZATION_ID=str(org.id))

    url = reverse("organizations:organization-detail")
    response = api_client.patch(url, {"description": "Malicious edit"}, format="json")
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_organization_members_list_and_add(authenticated_client):
    client = authenticated_client["client"]
    url = reverse("organizations:organization-members-list")
    response = client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 1

    # Add a new member
    post_data = {
        "email": "new.operator@alpha.io",
        "role": "operator",
        "first_name": "New",
        "last_name": "Operator",
    }
    create_resp = client.post(url, post_data, format="json")
    assert create_resp.status_code == status.HTTP_201_CREATED
    assert create_resp.data["user"]["email"] == "new.operator@alpha.io"
    assert create_resp.data["role"] == "operator"


@pytest.mark.django_db
def test_cannot_delete_last_admin(authenticated_client):
    client = authenticated_client["client"]
    membership = authenticated_client["membership"]

    url = reverse("organizations:organization-members-detail", kwargs={"pk": membership.id})
    response = client.delete(url)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Cannot remove the last administrator" in response.data["detail"]


@pytest.mark.django_db
def test_cross_tenant_member_access_isolation(api_client, user_factory, organization_factory, membership_factory):
    # Org A
    user_a = user_factory(email="admin@a.io")
    org_a = organization_factory(name="Org A", slug="org-a")
    membership_factory(organization=org_a, user=user_a, role="org_admin")

    # Org B
    user_b = user_factory(email="admin@b.io")
    org_b = organization_factory(name="Org B", slug="org-b")
    membership_b = membership_factory(organization=org_b, user=user_b, role="org_admin")

    # Authenticate as Org A
    token_a = str(RefreshToken.for_user(user_a).access_token)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_a}", HTTP_X_ORGANIZATION_ID=str(org_a.id))

    # Attempt to delete Org B's member
    url = reverse("organizations:organization-members-detail", kwargs={"pk": membership_b.id})
    response = api_client.delete(url)

    # Must be 404 Not Found to prevent ID enumeration across tenants
    assert response.status_code == status.HTTP_404_NOT_FOUND
