"""Admin-only views for managing users and admin roles."""
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.enums import UserType
from core.models import User
from core.permissions import IsAdminRole
from core.serializers import DetailResponseSerializer, MessageResponseSerializer

from .serializers import AdminUserSerializer


class AllUsersView(APIView):
    """GET /admin/users/"""
    permission_classes = [IsAdminRole]

    @extend_schema(tags=['admin'], responses={200: AdminUserSerializer(many=True)})
    def get(self, request):
        users = User.objects.all()
        serializer = AdminUserSerializer(users, many=True)
        return Response(serializer.data)


class PromoteToAdminView(APIView):
    """PATCH /admin/users/{id}/role/"""
    permission_classes = [IsAdminRole]

    @extend_schema(
        tags=['admin'],
        request=None,
        responses={
            200: MessageResponseSerializer,
            400: DetailResponseSerializer,
            404: DetailResponseSerializer,
        },
    )
    def patch(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            # Return a clean 404 instead of a server error.
            return Response(
                {'detail': 'user not found'}, status=status.HTTP_404_NOT_FOUND
            )
        if user.role == UserType.ADMIN:
            return Response(
                {'detail': 'user already has admin access'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.role = UserType.ADMIN
        user.save()
        return Response({'message': 'User promoted to admin successfully'})


class AllAdminsView(APIView):
    """GET /admin/"""
    permission_classes = [IsAdminRole]

    @extend_schema(tags=['admin'], responses={200: AdminUserSerializer(many=True)})
    def get(self, request):
        admins = User.objects.filter(role=UserType.ADMIN)
        serializer = AdminUserSerializer(admins, many=True)
        return Response(serializer.data)
