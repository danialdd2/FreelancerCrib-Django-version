"""Views for listing, creating, and managing projects."""
from django.db.models import Q
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.enums import BidStatus, NotificationType, ProjectStatus
from core.models import Bid, Notification, Project
from core.serializers import DetailResponseSerializer, MessageResponseSerializer

from .serializers import CreateProjectSerializer, ProjectSerializer

# Keep list pagination bounded so ?limit=100000 can't be used to pull the
# whole table in one request.
MAX_PAGE_LIMIT = 100


class ProjectListCreateView(APIView):
    """GET/POST /projects/"""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['projects'],
        parameters=[
            OpenApiParameter(
                'search', OpenApiTypes.STR, OpenApiParameter.QUERY,
                required=False,
                description='Case-insensitive match against title/description.',
            ),
            OpenApiParameter(
                'status', OpenApiTypes.STR, OpenApiParameter.QUERY,
                required=False, enum=[c.value for c in ProjectStatus],
                description='Filter by project status.',
            ),
            OpenApiParameter(
                'skip', OpenApiTypes.INT, OpenApiParameter.QUERY,
                required=False, description='Number of results to skip (default 0).',
            ),
            OpenApiParameter(
                'limit', OpenApiTypes.INT, OpenApiParameter.QUERY,
                required=False,
                description=f'Max results to return (default 10, max {MAX_PAGE_LIMIT}).',
            ),
        ],
        responses={200: ProjectSerializer(many=True)},
    )
    def get(self, request):
        queryset = Project.objects.all()

        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )

        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        skip, limit = self._parse_pagination(request)
        if skip is None:
            return Response(
                {'detail': 'skip and limit must be non-negative integers'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        queryset = queryset.order_by('id')[skip:skip + limit]

        serializer = ProjectSerializer(queryset, many=True)
        return Response(serializer.data)

    @staticmethod
    def _parse_pagination(request):
        """Safely parse ?skip=&limit=, returning (None, None) if invalid."""
        try:
            skip = int(request.query_params.get('skip', 0))
            limit = int(request.query_params.get('limit', 10))
        except (TypeError, ValueError):
            return None, None
        if skip < 0 or limit < 1:
            return None, None
        return skip, min(limit, MAX_PAGE_LIMIT)

    @extend_schema(
        tags=['projects'],
        request=CreateProjectSerializer,
        responses={201: MessageResponseSerializer},
    )
    def post(self, request):
        serializer = CreateProjectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        Project.objects.create(owner=request.user, **serializer.validated_data)
        return Response(
            {'message': 'Project created successfully.'},
            status=status.HTTP_201_CREATED,
        )


class MyProjectsView(APIView):
    """GET /projects/my/"""
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=['projects'], responses={200: ProjectSerializer(many=True)})
    def get(self, request):
        projects = Project.objects.filter(owner=request.user)
        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data)


class ProjectDetailView(APIView):
    """GET/PUT /projects/{id}/"""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['projects'],
        responses={200: ProjectSerializer, 404: DetailResponseSerializer},
    )
    def get(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response(
                {'detail': 'project not found !'}, status=status.HTTP_404_NOT_FOUND
            )
        serializer = ProjectSerializer(project)
        return Response(serializer.data)

    @extend_schema(
        tags=['projects'],
        request=CreateProjectSerializer,
        responses={
            200: MessageResponseSerializer,
            400: DetailResponseSerializer,
            404: DetailResponseSerializer,
        },
    )
    def put(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id, owner=request.user)
        except Project.DoesNotExist:
            return Response(
                {'detail': 'project not found !'}, status=status.HTTP_404_NOT_FOUND
            )
        if project.status != ProjectStatus.OPEN:
            return Response(
                {'detail': 'project status is not open !'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = CreateProjectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        for key, value in serializer.validated_data.items():
            setattr(project, key, value)
        project.save()
        return Response({'message': 'Project updated successfully.'})


class AcceptBidView(APIView):
    """
    PATCH /projects/{id}/bids/{bid_id}/accept/

    Marks one bid accepted, rejects the rest, sets the project winner,
    and notifies the freelancer.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['projects'],
        request=None,
        responses={
            200: MessageResponseSerializer,
            400: DetailResponseSerializer,
            404: DetailResponseSerializer,
        },
    )
    def patch(self, request, project_id, bid_id):
        try:
            project = Project.objects.get(id=project_id, owner=request.user)
        except Project.DoesNotExist:
            return Response(
                {'detail': 'project not found !'}, status=status.HTTP_404_NOT_FOUND
            )
        if project.status != ProjectStatus.OPEN:
            return Response(
                {'detail': 'project is already taken !'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            bid = Bid.objects.get(id=bid_id, project_id=project_id)
        except Bid.DoesNotExist:
            return Response(
                {'detail': 'bid not found !'}, status=status.HTTP_404_NOT_FOUND
            )

        bid.status = BidStatus.ACCEPTED
        bid.save()

        Bid.objects.filter(project_id=project_id).exclude(id=bid_id).update(
            status=BidStatus.REJECTED
        )

        project.winner_id = bid.freelancer_id
        project.status = ProjectStatus.IN_PROGRESS
        project.save()

        Notification.objects.create(
            user_id=bid.freelancer_id,
            title='bid accepted',
            message='Congratulations! Your bid has been accepted.',
            type=NotificationType.BID_ACCEPTED,
        )

        return Response(
            {'message': 'Bid accepted successfully.'},
            status=status.HTTP_200_OK,
        )


class CompleteProjectView(APIView):
    """PATCH /projects/{id}/complete/"""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['projects'],
        request=None,
        responses={
            200: MessageResponseSerializer,
            400: DetailResponseSerializer,
            404: DetailResponseSerializer,
        },
    )
    def patch(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id, owner=request.user)
        except Project.DoesNotExist:
            return Response(
                {'detail': 'project not found !'}, status=status.HTTP_404_NOT_FOUND
            )
        if project.status == ProjectStatus.COMPLETED:
            return Response(
                {'detail': 'project is already complete.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if project.status != ProjectStatus.IN_PROGRESS:
            return Response(
                {'detail': 'project is not in progress to be completed.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        Notification.objects.create(
            user_id=project.owner_id,
            title='project completed',
            message='Project completed successfully.',
            type=NotificationType.PROJECT_COMPLETED,
        )
        Notification.objects.create(
            user_id=project.winner_id,
            title='project completed',
            message='Project completed successfully.',
            type=NotificationType.PROJECT_COMPLETED,
        )
        project.status = ProjectStatus.COMPLETED
        project.save()
        return Response({'message': 'Project completed successfully.'})


class CancelProjectView(APIView):
    """PATCH /projects/{id}/cancel/"""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['projects'],
        request=None,
        responses={
            200: MessageResponseSerializer,
            400: DetailResponseSerializer,
            404: DetailResponseSerializer,
        },
    )
    def patch(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id, owner=request.user)
        except Project.DoesNotExist:
            return Response(
                {'detail': 'project not found !'}, status=status.HTTP_404_NOT_FOUND
            )
        if project.status == ProjectStatus.CANCELED:
            return Response(
                {'detail': 'project is already canceled.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if project.status in (ProjectStatus.COMPLETED, ProjectStatus.IN_PROGRESS):
            return Response(
                {'detail': 'project cannot be canceled.'},
                status=status.HTTP_400_BAD_REQUEST,
            )


        Bid.objects.filter(project_id=project_id).update(
            status=BidStatus.REJECTED
        )
        project.status = ProjectStatus.CANCELED
        project.save()
        return Response({'message': 'project canceled successfully.'})
