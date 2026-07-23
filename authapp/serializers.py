"""Serializers for the login/token endpoint."""
from rest_framework import serializers


class LoginSerializer(serializers.Serializer):
    """Username/password input for obtaining an access token."""
    username = serializers.CharField()
    password = serializers.CharField(style={'input_type': 'password'}, trim_whitespace=False)


class TokenSerializer(serializers.Serializer):
    """Shape of the access token response."""
    access_token = serializers.CharField()
    token_type = serializers.CharField()
