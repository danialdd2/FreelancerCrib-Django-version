"""Views for user registration and profile management."""
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import User
from core.serializers import DetailResponseSerializer, MessageResponseSerializer

from .serializers import (
    ChangeInfoSerializer,
    CreateUserSerializer,
    PublicUserSerializer,
    UserResponseSerializer,
)


class CreateUserView(APIView):
    """POST /user/"""
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['users'],
        request=CreateUserSerializer,
        responses={201: MessageResponseSerializer},
    )
    def post(self, request):
        serializer = CreateUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {'message': 'User created successfully'},
            status=status.HTTP_201_CREATED,
        )


class MeView(APIView):
    """GET/PUT /user/me/"""
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=['users'], responses={200: UserResponseSerializer})
    def get(self, request):
        serializer = UserResponseSerializer(request.user)
        return Response(serializer.data)

    @extend_schema(
        tags=['users'],
        request=ChangeInfoSerializer,
        responses={200: MessageResponseSerializer},
    )
    def put(self, request):
        serializer = ChangeInfoSerializer(
            request.user, data=request.data, partial=False
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Profile updated successfully'})


class UserDetailView(APIView):
    """GET /user/{user_id}/"""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['users'],
        responses={200: PublicUserSerializer, 404: DetailResponseSerializer},
    )
    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:

            return Response(
                {'detail': 'user not found'},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = PublicUserSerializer(user)
        return Response(serializer.data)
