"""
Root URL configuration.

Each domain area of the API (auth, users, projects, bids, ratings,
notifications, admin, dashboard) lives in its own Django app and is
wired in below.

NOTE: the API's own admin endpoints live at "/admin/" (see adminpanel/).
Django's built-in admin site has been moved to "/django-admin/" instead
of the default "/admin/" to avoid clashing with those routes.
"""
from django.contrib import admin
from django.urls import include, path

from bids.views import BidDetailView, MyBidsView, ProjectBidsView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path('django-admin/', admin.site.urls),

    path('api/schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path(
        'api/docs/',
        SpectacularSwaggerView.as_view(url_name='api-schema'),
        name='api-docs',
    ),
    path(
        'api/redoc/',
        SpectacularRedocView.as_view(url_name='api-schema'),
        name='api-redoc',
    ),

    path('auth/', include('authapp.urls')),
    path('user/', include('users.urls')),
    path('projects/', include('projects.urls')),
    path('projects/', include('ratings.urls')),


    path(
        'projects/<int:project_id>/bids/',
        ProjectBidsView.as_view(),
        name='project-bids',
    ),
    path('bids/<int:bid_id>/', BidDetailView.as_view(), name='bid-detail'),
    path('users/me/bids/', MyBidsView.as_view(), name='my-bids'),

    path('notifications/', include('notifications.urls')),
    path('admin/', include('adminpanel.urls')),
    path('dashboard/', include('dashboard.urls')),
]
