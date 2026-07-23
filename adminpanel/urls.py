from django.urls import path

from .views import AllAdminsView, AllUsersView, PromoteToAdminView

app_name = 'adminpanel'

urlpatterns = [
    path('', AllAdminsView.as_view(), name='all-admins'),
    path('users/', AllUsersView.as_view(), name='all-users'),
    path(
        'users/<int:user_id>/role/',
        PromoteToAdminView.as_view(),
        name='promote',
    ),
]
