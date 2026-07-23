from django.urls import path

from .views import (
    NotificationDetailView,
    NotificationListView,
    ReadAllNotificationsView,
    ReadNotificationView,
    UnreadCountView,
    UnreadNotificationsView,
)

app_name = 'notifications'

urlpatterns = [
    path('', NotificationListView.as_view(), name='list'),
    path('unread/', UnreadNotificationsView.as_view(), name='unread'),
    path('unread-count/', UnreadCountView.as_view(), name='unread-count'),
    path('read-all/', ReadAllNotificationsView.as_view(), name='read-all'),
    path(
        '<int:notification_id>/read/',
        ReadNotificationView.as_view(),
        name='read',
    ),
    path(
        '<int:notification_id>/',
        NotificationDetailView.as_view(),
        name='detail',
    ),
]
