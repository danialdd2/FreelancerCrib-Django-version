"""Response shapes for the client and freelancer dashboards."""
from rest_framework import serializers


class ClientDashboardSerializer(serializers.Serializer):
    projects_created = serializers.IntegerField()
    projects_completed = serializers.IntegerField()
    client_open_projects = serializers.IntegerField()
    active_projects = serializers.IntegerField()
    total_bids = serializers.IntegerField()
    rating = serializers.FloatField()


class FreelancerDashboardSerializer(serializers.Serializer):
    bids_sent = serializers.IntegerField()
    pending_bids = serializers.IntegerField()
    projects_won = serializers.IntegerField()
    projects_completed = serializers.IntegerField()
    active_projects = serializers.IntegerField()
    rating = serializers.FloatField()
