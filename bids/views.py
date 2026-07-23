"""Views for submitting, listing, updating, and deleting bids."""
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.enums import BidStatus, NotificationType, ProjectStatus
from core.models import Bid, Notification, Project
from core.serializers import DetailResponseSerializer, MessageResponseSerializer

from .serializers import BidSerializer, CreateBidSerializer


class ProjectBidsView(APIView):
    """
    POST/GET /projects/{project_id}/bids/

    Handles submitting a new bid and listing bids on a project.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['bids'],
        request=CreateBidSerializer,
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
            return Response(status=status.HTTP_404_NOT_FOUND)

        if project.owner_id == request.user.id:
            return Response(
                {'detail': 'you cant send bid on your project'},
                status=status.HTTP_403_FORBIDDEN,
            )
        if project.status in (ProjectStatus.CANCELED, ProjectStatus.COMPLETED):
            return Response(
                {'detail': 'project is canceled or completed'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if Bid.objects.filter(project_id=project_id, freelancer=request.user).exists():
            return Response(
                {'detail': 'you have already sent bid on this project'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = CreateBidSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        Bid.objects.create(
            price=serializer.validated_data['price'],
            message=serializer.validated_data['message'],
            project=project,
            freelancer=request.user,
        )
        Notification.objects.create(
            user_id=project.owner_id,
            title='new bid',
            message='you have a new bid request',
            type=NotificationType.NEW_BID,
        )
        return Response(
            {'message': 'Bid submitted successfully'},
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        tags=['bids'],
        responses={200: BidSerializer(many=True), 404: DetailResponseSerializer},
    )
    def get(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id, owner=request.user)
        except Project.DoesNotExist:
            return Response(
                {'detail': 'project not found'}, status=status.HTTP_404_NOT_FOUND
            )
        bids = Bid.objects.filter(project_id=project_id)
        if not bids.exists():
            return Response(
                {'detail': 'no bids on this project yet ):'},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = BidSerializer(bids, many=True)
        return Response(serializer.data)


class MyBidsView(APIView):
    """GET /users/me/bids/"""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['bids'],
        responses={200: BidSerializer(many=True), 404: DetailResponseSerializer},
    )
    def get(self, request):
        bids = Bid.objects.filter(freelancer=request.user)
        if not bids.exists():
            return Response(
                {'detail': 'you have no bids'}, status=status.HTTP_404_NOT_FOUND
            )
        serializer = BidSerializer(bids, many=True)
        return Response(serializer.data)


class BidDetailView(APIView):
    """PUT/DELETE /bids/{bid_id}/"""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['bids'],
        request=CreateBidSerializer,
        responses={
            200: MessageResponseSerializer,
            400: DetailResponseSerializer,
            404: DetailResponseSerializer,
        },
    )
    def put(self, request, bid_id):
        try:
            bid = Bid.objects.get(id=bid_id, freelancer=request.user)
        except Bid.DoesNotExist:
            return Response(
                {'detail': 'bid not found'}, status=status.HTTP_404_NOT_FOUND
            )
        # BUG FIX: previously a bid could be edited after it had already
        # been accepted or rejected, silently changing the price/message
        # on a bid the project owner already acted on.
        if bid.status != BidStatus.PENDING:
            return Response(
                {'detail': 'only pending bids can be edited'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = CreateBidSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        for key, value in serializer.validated_data.items():
            setattr(bid, key, value)
        bid.save()
        return Response({'message': 'Bid updated successfully'})

    @extend_schema(
        tags=['bids'],
        request=None,
        responses={
            200: MessageResponseSerializer,
            400: DetailResponseSerializer,
            404: DetailResponseSerializer,
        },
    )
    def delete(self, request, bid_id):
        try:
            bid = Bid.objects.get(id=bid_id, freelancer=request.user)
        except Bid.DoesNotExist:
            return Response(
                {'detail': 'bid not found'}, status=status.HTTP_404_NOT_FOUND
            )
        # BUG FIX: same issue as put() above - don't allow deleting a bid
        # that has already been accepted/rejected.
        if bid.status != BidStatus.PENDING:
            return Response(
                {'detail': 'only pending bids can be deleted'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        bid.delete()
        return Response({'message': 'Bid deleted successfully'})
