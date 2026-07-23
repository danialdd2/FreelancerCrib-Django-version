"""Input validation for submitting a rating."""
from rest_framework import serializers


class CreateRatingSerializer(serializers.Serializer):
    score = serializers.IntegerField(min_value=1, max_value=10)
    comment = serializers.CharField(allow_blank=True)
