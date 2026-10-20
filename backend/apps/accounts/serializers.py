from apps.organizations.models import Organization, OrganizationMembership
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "is_active",
            "is_platform_admin",
            "date_joined",
        ]
        read_only_fields = ["id", "is_platform_admin", "date_joined"]


class OrganizationBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ["id", "name", "slug", "timezone"]


class MembershipBriefSerializer(serializers.ModelSerializer):
    organization = OrganizationBriefSerializer(read_only=True)

    class Meta:
        model = OrganizationMembership
        fields = ["id", "organization", "role", "is_active", "joined_at"]


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Augments JWT authentication response with user profile and organization memberships."""

    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user

        memberships = OrganizationMembership.objects.filter(
            user=user,
            is_active=True,
            organization__is_active=True,
        ).select_related("organization")

        membership_data = MembershipBriefSerializer(memberships, many=True).data

        # Determine default active tenant
        default_membership = memberships.first()
        active_org = OrganizationBriefSerializer(default_membership.organization).data if default_membership else None
        active_role = default_membership.role if default_membership else None

        data["user"] = UserSerializer(user).data
        data["memberships"] = membership_data
        data["active_organization"] = active_org
        data["active_role"] = active_role

        return data
