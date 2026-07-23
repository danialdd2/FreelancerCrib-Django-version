"""
Domain models for the freelance marketplace: users, projects, bids,
ratings and notifications.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models

from core.enums import BidStatus, NotificationType, ProjectStatus, UserType


class User(AbstractUser):
    """Custom user model with role/user_role fields for auth and permissions."""
    full_name = models.CharField(max_length=150, blank=True)
    role = models.CharField(
        max_length=20, choices=UserType.choices, default=UserType.USER
    )
    user_role = models.CharField(
        max_length=20, choices=UserType.choices, default=UserType.CLIENT
    )

    def __str__(self):
        return self.username


class Project(models.Model):
    """A project posted by a client, open for freelancer bids."""
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    budget = models.IntegerField()
    status = models.CharField(
        max_length=20, choices=ProjectStatus.choices, default=ProjectStatus.OPEN
    )
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='projects_owned'
    )
    winner = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='projects_won'
    )

    def __str__(self):
        return self.title


class Bid(models.Model):
    """A freelancer's price/message offer on a project."""
    price = models.FloatField()
    message = models.CharField(max_length=255, blank=True)
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='bids'
    )
    freelancer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='bids'
    )
    status = models.CharField(
        max_length=20, choices=BidStatus.choices, default=BidStatus.PENDING
    )

    def __str__(self):
        return f'Bid #{self.pk} on {self.project_id}'


class Rating(models.Model):
    """A rating left by one user for another after a completed project."""
    score = models.IntegerField()
    comment = models.TextField(blank=True)
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='ratings'
    )
    from_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='ratings_given'
    )
    to_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='ratings_received'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Rating #{self.pk} ({self.score})'


class Notification(models.Model):
    """An in-app notification for a user."""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='notifications'
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    type = models.CharField(max_length=30, choices=NotificationType.choices)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
