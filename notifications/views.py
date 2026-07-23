"""Views for listing, reading, and deleting notifications."""
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Notification
from core.serializers import CountResponseSerializer, DetailResponseSerializer, MessageResponseSerializer

from .serializers import NotificationSerializer


class NotificationListView(APIView):
    """GET /notifications/"""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['notifications'],
        responses={
            200: NotificationSerializer(many=True),
            404: DetailResponseSerializer,
        },
    )
    def get(self, request):
        messages = Notification.objects.filter(user=request.user)
        if not messages.exists():
            return Response(
                {'detail': 'no new notifications'}, status=status.HTTP_404_NOT_FOUND
            )
        serializer = NotificationSerializer(messages, many=True)
        return Response(serializer.data)


class UnreadNotificationsView(APIView):
    """GET /notifications/unread/"""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['notifications'],
        responses={
            200: NotificationSerializer(many=True),
            404: DetailResponseSerializer,
        },
    )
    def get(self, request):
        messages = Notification.objects.filter(user=request.user, is_read=False)
        if not messages.exists():
            return Response(
                {'detail': 'no new notifications'}, status=status.HTTP_404_NOT_FOUND
            )
        serializer = NotificationSerializer(messages, many=True)
        return Response(serializer.data)


class UnreadCountView(APIView):
    """GET /notifications/unread-count/"""
    permission_classes = [IsAuthenticated]

    @extend_schema(tags=['notifications'], responses={200: CountResponseSerializer})
    def get(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()
 
        return Response({'count': count})


class ReadNotificationView(APIView):
    """PATCH /notifications/{id}/read/"""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['notifications'],
        request=None,
        responses={200: NotificationSerializer, 404: DetailResponseSerializer},
    )
    def patch(self, request, notification_id):
        try:
            message = Notification.objects.get(
                user=request.user, id=notification_id
            )
        except Notification.DoesNotExist:
            return Response(
                {'detail': 'notification not found'},
                status=status.HTTP_404_NOT_FOUND,
            )
        message.is_read = True
        message.save()
        serializer = NotificationSerializer(message)
        return Response(serializer.data)


class ReadAllNotificationsView(APIView):
    """PATCH /notifications/read-all/"""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['notifications'],
        request=None,
        responses={200: MessageResponseSerializer},
    )
    def patch(self, request):
        Notification.objects.filter(user=request.user).update(is_read=True)
        # BUG FIX: was Response('messages read succesfully') - a bare
        # string instead of the {"message": ...} shape used everywhere else.
        return Response({'message': 'messages read successfully'})


class NotificationDetailView(APIView):
    """DELETE /notifications/{id}/"""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['notifications'],
        request=None,
        responses={
            200: MessageResponseSerializer,
            404: DetailResponseSerializer,
        },
    )
    def delete(self, request, notification_id):
        try:
            message = Notification.objects.get(
                user=request.user, id=notification_id
            )
        except Notification.DoesNotExist:
            return Response(
                {'detail': 'notification not found'},
                status=status.HTTP_404_NOT_FOUND,
            )
        message.delete()
        # BUG FIX: was Response('message deleted succesfully') - bare string.
        return Response({'message': 'message deleted successfully'})
