from apps.accounts.serializers import UserSerializer
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from .models import Organization, OrganizationMembership

User = get_user_model()


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "timezone",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "is_active", "created_at", "updated_at"]


class OrganizationMembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = OrganizationMembership
        fields = [
            "id",
            "user",
            "role",
            "is_active",
            "joined_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "joined_at", "created_at", "updated_at"]


class AddMemberSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(
        choices=OrganizationMembership.Role.choices,
        default=OrganizationMembership.Role.VIEWER,
    )
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)

    def validate(self, attrs):
        org = self.context["organization"]
        email = attrs["email"].lower().strip()
        user = User.objects.filter(email=email).first()
        if (
            user
            and OrganizationMembership.objects.filter(
                organization=org, user=user
            ).exists()
        ):
            raise serializers.ValidationError(
                {"email": "This user is already a member of the organization."}
            )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        org = self.context["organization"]
        email = validated_data["email"].lower().strip()
        user = User.objects.filter(email=email).first()
        if not user:
            user = User.objects.create_user(
                email=email,
                first_name=validated_data.get("first_name", ""),
                last_name=validated_data.get("last_name", ""),
            )
        membership = OrganizationMembership.objects.create(
            organization=org,
            user=user,
            role=validated_data["role"],
        )
        return membership


class UpdateMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationMembership
        fields = ["role", "is_active"]

    def validate(self, attrs):
        instance = self.instance
        new_role = attrs.get("role", instance.role)
        new_active = attrs.get("is_active", instance.is_active)

        # Check last active org_admin constraint
        if instance.role == OrganizationMembership.Role.ORG_ADMIN and (
            new_role != OrganizationMembership.Role.ORG_ADMIN or not new_active
        ):
            remaining = (
                OrganizationMembership.objects.filter(
                    organization=instance.organization,
                    role=OrganizationMembership.Role.ORG_ADMIN,
                    is_active=True,
                )
                .exclude(pk=instance.pk)
                .count()
            )
            if remaining == 0:
                raise serializers.ValidationError(
                    "Cannot demote or deactivate the last administrator of the organization."
                )
        return attrs
