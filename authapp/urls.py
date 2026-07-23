from django.urls import path

from .views import LoginView

app_name = 'auth'

urlpatterns = [
    path('token/', LoginView.as_view(), name='token'),
]
