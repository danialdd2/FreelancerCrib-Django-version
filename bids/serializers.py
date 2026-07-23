"""Serializers for submitting and representing bids."""
from rest_framework import serializers

from core.models import Bid


class CreateBidSerializer(serializers.Serializer):
    """Input validation for submitting/updating a bid."""
    price = serializers.FloatField(min_value=0.01)
    message = serializers.CharField(min_length=5, max_length=50)


class BidSerializer(serializers.ModelSerializer):
    """Bid representation returned by the API."""

    class Meta:
        model = Bid
        fields = ('id', 'price', 'message', 'project_id')
