"""View for submitting a rating after project completion."""
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.enums import NotificationType, ProjectStatus
from core.models import Notification, Project, Rating
from core.serializers import DetailResponseSerializer, MessageResponseSerializer

from .serializers import CreateRatingSerializer


class CreateRatingView(APIView):
    """POST /projects/{project_id}/ratings/"""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['ratings'],
        request=CreateRatingSerializer,
        responses={
            201: MessageResponseSerializer,
            400: DetailResponseSerializer,
            403: DetailResponseSerializer,
            404: DetailResponseSerializer,
        },
    )
    def post(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response(
                {'detail': 'project not found !'}, status=status.HTTP_404_NOT_FOUND
            )

        user_id = request.user.id
        if user_id not in (project.owner_id, project.winner_id):
            return Response(
                {'detail': 'project not found !'}, status=status.HTTP_403_FORBIDDEN
            )
        if project.status != ProjectStatus.COMPLETED:
            return Response(
                {'detail': 'project has to be completed'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        to_user_id = (
            project.winner_id if user_id == project.owner_id else project.owner_id
        )

        if Rating.objects.filter(project_id=project.id, from_user_id=user_id).exists():
            return Response(
                {'detail': 'You have already rated this project.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = CreateRatingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        Rating.objects.create(
            project=project,
            score=serializer.validated_data['score'],
            comment=serializer.validated_data['comment'],
            from_user_id=user_id,
            to_user_id=to_user_id,
        )
        Notification.objects.create(
            user_id=to_user_id,
            title='new rating',
            message='You received a new rating.',
            type=NotificationType.RATING_RECEIVED,
        )
        return Response(
            {'message': 'Rating submitted successfully'},
            status=status.HTTP_201_CREATED,
        )
