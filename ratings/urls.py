from django.urls import path

from .views import CreateRatingView

app_name = 'ratings'

urlpatterns = [
    path(
        '<int:project_id>/ratings/', CreateRatingView.as_view(), name='create'
    ),
]
