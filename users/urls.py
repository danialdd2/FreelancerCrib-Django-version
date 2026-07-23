from django.urls import path

from .views import CreateUserView, MeView, UserDetailView

app_name = 'users'

urlpatterns = [
    path('', CreateUserView.as_view(), name='create'),
    path('me/', MeView.as_view(), name='me'),
    path('<int:user_id>/', UserDetailView.as_view(), name='detail'),
]
