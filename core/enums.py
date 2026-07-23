"""
Choice enums used across the project's models.
"""
from django.db import models


class NotificationType(models.TextChoices):
    NEW_BID = 'new_bid', 'New bid'
    BID_ACCEPTED = 'bid_accepted', 'Bid accepted'
    PROJECT_COMPLETED = 'project_completed', 'Project completed'
    RATING_RECEIVED = 'rating_received', 'Rating received'


class UserType(models.TextChoices):
    CLIENT = 'client', 'Client'
    USER = 'user', 'User'
    ADMIN = 'admin', 'Admin'
    FREELANCER = 'freelancer', 'Freelancer'


class ProjectStatus(models.TextChoices):
    OPEN = 'open', 'Open'
    IN_PROGRESS = 'in_progress', 'In progress'
    COMPLETED = 'completed', 'Completed'
    CANCELED = 'canceled', 'Canceled'


class BidStatus(models.TextChoices):
    ACCEPTED = 'accepted', 'Accepted'
    REJECTED = 'rejected', 'Rejected'
    PENDING = 'pending', 'Pending'
