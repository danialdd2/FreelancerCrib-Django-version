"""Serializers for project creation and responses."""
from rest_framework import serializers

from core.models import Project


class CreateProjectSerializer(serializers.Serializer):
    """Input validation for creating/updating a project."""
    title = serializers.CharField(min_length=5, max_length=20)
    description = serializers.CharField(min_length=8, max_length=50)
    budget = serializers.IntegerField(min_value=1)


class ProjectSerializer(serializers.ModelSerializer):
    """Project representation used for list and detail responses."""

    class Meta:
        model = Project
        fields = ('id', 'title', 'description', 'budget', 'status', 'winner')
