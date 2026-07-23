"""
Small, reusable response-shape serializers.

Several views return simple {"message": ...} / {"detail": ...} / {"count": ...}
payloads. These serializers exist purely so drf-spectacular can document those
response shapes correctly (instead of showing "no parameters" / an untyped
response), and so every view returns a consistent, predictable body instead of
a bare string or int.
"""
from rest_framework import serializers


class MessageResponseSerializer(serializers.Serializer):
    """Generic {"message": "..."} success payload."""
    message = serializers.CharField()


class DetailResponseSerializer(serializers.Serializer):
    """Generic {"detail": "..."} error payload."""
    detail = serializers.CharField()


class CountResponseSerializer(serializers.Serializer):
    """Generic {"count": N} payload."""
    count = serializers.IntegerField()
