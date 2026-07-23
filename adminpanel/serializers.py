"""Reuses UserResponseSerializer-style output for the admin endpoints"""
from rest_framework import serializers

from core.models import User


class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'full_name', 'role', 'user_role', 'is_active')
