"""View returning role-specific dashboard statistics."""
from django.db.models import Avg
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.enums import BidStatus, ProjectStatus, UserType
from core.models import Bid, Project, Rating

from .serializers import ClientDashboardSerializer, FreelancerDashboardSerializer

# GET /dashboard/ returns one of two different shapes depending on the
# caller's role (see ClientDashboardSerializer vs FreelancerDashboardSerializer).
# Swagger can only document one concrete schema per status code here, so it
# shows the client shape and the description below spells out the
# freelancer fields explicitly instead.
_FREELANCER_FIELDS = ', '.join(FreelancerDashboardSerializer().fields)


class DashboardView(APIView):
    """GET /dashboard/"""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['dashboard'],
        responses={200: ClientDashboardSerializer},
        description=(
            'Response shape depends on the caller\'s role. Clients get the '
            'fields shown below. Freelancers instead get: '
            f'{_FREELANCER_FIELDS}.'
        ),
    )
    def get(self, request):
        user = request.user

        # BUG FIX: compared user.user_role against the hardcoded string
        # 'client' instead of the UserType enum used everywhere else in
        # the codebase. Same value today, but easy to typo/drift over time.
        if user.user_role == UserType.CLIENT:
            projects_created = Project.objects.filter(owner=user).count()
            projects_completed = Project.objects.filter(
                owner=user, status=ProjectStatus.COMPLETED
            ).count()
            active_projects = Project.objects.filter(
                owner=user, status=ProjectStatus.IN_PROGRESS
            ).count()
            total_bids = Bid.objects.filter(project__owner=user).count()
            rating = Rating.objects.filter(to_user=user).aggregate(
                avg=Avg('score')
            )['avg'] or 0
            open_projects = Project.objects.filter(
                owner=user, status=ProjectStatus.OPEN
            ).count()

            data = {
                'projects_created': projects_created,
                'projects_completed': projects_completed,
                'client_open_projects': open_projects,
                'active_projects': active_projects,
                'total_bids': total_bids,
                'rating': rating,
            }
            serializer = ClientDashboardSerializer(data)
        else:
            active_projects = Project.objects.filter(
                winner=user, status=ProjectStatus.IN_PROGRESS
            ).count()
            projects_completed = Project.objects.filter(
                winner=user, status=ProjectStatus.COMPLETED
            ).count()
            bids_sent = Bid.objects.filter(freelancer=user).count()
            rating = Rating.objects.filter(to_user=user).aggregate(
                avg=Avg('score')
            )['avg'] or 0
            projects_won = Project.objects.filter(winner=user).count()
            pending_bids = Bid.objects.filter(
                freelancer=user, status=BidStatus.PENDING
            ).count()

            data = {
                'bids_sent': bids_sent,
                'pending_bids': pending_bids,
                'projects_won': projects_won,
                'projects_completed': projects_completed,
                'active_projects': active_projects,
                'rating': rating,
            }
            serializer = FreelancerDashboardSerializer(data)

        return Response(serializer.data)
