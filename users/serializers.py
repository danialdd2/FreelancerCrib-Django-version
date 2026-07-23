"""Serializers for user registration and profile management."""
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

User = get_user_model()


class CreateUserSerializer(serializers.ModelSerializer):
    """Input validation for registering a new user."""

    username = serializers.CharField(
        min_length=5, max_length=20,
        validators=[UniqueValidator(queryset=User.objects.all())],
    )
    full_name = serializers.CharField(min_length=5, max_length=20)
    password = serializers.CharField(
        min_length=8, max_length=15, write_only=True, style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'full_name', 'password', 'user_role')

    def create(self, validated_data):
        password = validated_data.pop('password')
        return User.objects.create_user(password=password, **validated_data)


class ChangeInfoSerializer(serializers.ModelSerializer):
    """Input validation for updating profile info."""

    username = serializers.CharField(
        min_length=5, max_length=20,
        validators=[UniqueValidator(queryset=User.objects.all())],
    )
    full_name = serializers.CharField(min_length=5, max_length=20)

    class Meta:
        model = User
        fields = ('username', 'email', 'full_name')


class UserResponseSerializer(serializers.ModelSerializer):
    """Full profile representation, returned to the authenticated user."""

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'full_name', 'user_role', 'is_active')


class PublicUserSerializer(serializers.ModelSerializer):
    """Public profile representation, returned for GET /user/{id}."""
    created_at = serializers.DateTimeField(source='date_joined')

    class Meta:
        model = User
        fields = ('id', 'username', 'full_name', 'user_role', 'created_at')
