"""Tests for the core domain models."""
from django.contrib.auth import get_user_model
from django.test import TestCase

from core.enums import ProjectStatus, UserType
from core.models import Bid, Project

User = get_user_model()


class UserModelTests(TestCase):
    def test_create_user_hashes_password(self):
        """Creating a user stores a hashed password, not the raw value."""
        user = User.objects.create_user(
            username='client1',
            email='client1@example.com',
            password='testpass123',
            full_name='Client One',
            user_role=UserType.CLIENT,
        )
        self.assertNotEqual(user.password, 'testpass123')
        self.assertTrue(user.check_password('testpass123'))
        self.assertEqual(user.user_role, UserType.CLIENT)
        self.assertEqual(user.role, UserType.USER)  # default, not admin


class ProjectModelTests(TestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(
            username='client1', password='testpass123', user_role=UserType.CLIENT
        )

    def test_new_project_defaults_to_open(self):
        project = Project.objects.create(
            title='Build a landing page',
            description='Simple marketing site',
            budget=200,
            owner=self.client_user,
        )
        self.assertEqual(project.status, ProjectStatus.OPEN)
        self.assertIsNone(project.winner)


class BidModelTests(TestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(
            username='client1', password='testpass123', user_role=UserType.CLIENT
        )
        self.freelancer = User.objects.create_user(
            username='freelancer1', password='testpass123',
            user_role=UserType.FREELANCER,
        )
        self.project = Project.objects.create(
            title='Build a landing page', description='desc', budget=200,
            owner=self.client_user,
        )

    def test_bid_defaults_to_pending(self):
        bid = Bid.objects.create(
            price=150.0, message='I can do this', project=self.project,
            freelancer=self.freelancer,
        )
        self.assertEqual(bid.status, 'pending')
