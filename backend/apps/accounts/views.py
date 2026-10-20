from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import permissions, status, views
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import (
    CustomTokenObtainPairSerializer,
    MembershipBriefSerializer,
    OrganizationBriefSerializer,
    UserSerializer,
)


class LoginView(TokenObtainPairView):
    """Authenticates a user and returns JWT tokens along with tenant memberships."""

    serializer_class = CustomTokenObtainPairSerializer


class MeView(views.APIView):
    """Retrieves or updates the authenticated user's profile and active tenant context."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Get current user context",
        responses={200: OpenApiResponse(description="User profile and tenant context")},
    )
    def get(self, request):
        user = request.user
        from apps.common.authentication import resolve_tenant_context

        active_org, active_membership = resolve_tenant_context(request, user)
        request.tenant = active_org
        request.membership = active_membership

        memberships = user.memberships.filter(
            is_active=True,
            organization__is_active=True,
        ).select_related("organization")

        return Response(
            {
                "user": UserSerializer(user).data,
                "memberships": MembershipBriefSerializer(memberships, many=True).data,
                "active_organization": OrganizationBriefSerializer(active_org).data
                if active_org
                else None,
                "active_role": active_membership.role if active_membership else None,
            }
        )

    @extend_schema(
        summary="Update current user profile",
        request=UserSerializer,
        responses={200: UserSerializer},
    )
    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class LogoutView(views.APIView):
    """Revokes the refresh token and clears the authenticated session."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Logout and revoke refresh token",
        responses={200: OpenApiResponse(description="Token revoked successfully")},
    )
    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"error": "Refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {"message": "Successfully logged out."}, status=status.HTTP_200_OK
            )
        except Exception:
            return Response(
                {"error": "Invalid or expired token."},
                status=status.HTTP_400_BAD_REQUEST,
            )
