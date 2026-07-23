"""Tests for GET /dashboard/, which returns a different shape per role."""
from rest_framework import status

from core.enums import ProjectStatus
from core.models import Bid, Project, Rating
from core.tests.helpers import AuthenticatedAPITestCase


class ClientDashboardTests(AuthenticatedAPITestCase):
    def test_client_dashboard_shape_and_counts(self):
        owner = self.create_and_login('client1', 'client')
        Project.objects.create(
            title='Open one', description='desc', budget=100, owner=owner,
        )
        Project.objects.create(
            title='Completed one', description='desc', budget=100, owner=owner,
            status=ProjectStatus.COMPLETED,
        )

        res = self.client.get('/dashboard/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(
            set(res.data.keys()),
            {
                'projects_created', 'projects_completed', 'client_open_projects',
                'active_projects', 'total_bids', 'rating',
            },
        )
        self.assertEqual(res.data['projects_created'], 2)
        self.assertEqual(res.data['projects_completed'], 1)
        self.assertEqual(res.data['client_open_projects'], 1)


class FreelancerDashboardTests(AuthenticatedAPITestCase):
    def test_freelancer_dashboard_shape_and_counts(self):
        owner = self.create_and_login('client1', 'client')
        project = Project.objects.create(
            title='Landing page', description='desc', budget=100, owner=owner,
        )
        freelancer = self.create_and_login('freelancer1', 'freelancer')
        Bid.objects.create(
            price=90, message='pick me please', project=project,
            freelancer=freelancer,
        )

        res = self.client.get('/dashboard/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(
            set(res.data.keys()),
            {
                'bids_sent', 'pending_bids', 'projects_won',
                'projects_completed', 'active_projects', 'rating',
            },
        )
        self.assertEqual(res.data['bids_sent'], 1)
        self.assertEqual(res.data['pending_bids'], 1)

    def test_dashboard_requires_authentication(self):
        res = self.client.get('/dashboard/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
