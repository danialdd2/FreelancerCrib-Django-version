from django.urls import path

from .views import (
    AcceptBidView,
    CancelProjectView,
    CompleteProjectView,
    MyProjectsView,
    ProjectDetailView,
    ProjectListCreateView,
)

app_name = 'projects'

urlpatterns = [
    path('', ProjectListCreateView.as_view(), name='list-create'),
    path('my/', MyProjectsView.as_view(), name='my'),
    path('<int:project_id>/', ProjectDetailView.as_view(), name='detail'),
    path(
        '<int:project_id>/bids/<int:bid_id>/accept/',
        AcceptBidView.as_view(),
        name='accept-bid',
    ),
    path(
        '<int:project_id>/complete/',
        CompleteProjectView.as_view(),
        name='complete',
    ),
    path('<int:project_id>/cancel/', CancelProjectView.as_view(), name='cancel'),
]
