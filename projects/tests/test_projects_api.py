"""Tests for project creation, listing, and bidding/cancel flows."""
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from core.enums import BidStatus, ProjectStatus
from core.models import Bid, Project
from core.tests.helpers import AuthenticatedAPITestCase

User = get_user_model()


class ProjectCreateListTests(AuthenticatedAPITestCase):
    def test_create_project_requires_auth(self):
        self.client.credentials()  # no token
        res = self.client.post(
            '/projects/',
            {'title': 'Landing page', 'description': 'Build one', 'budget': 100},
        )
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_and_list_project(self):
        self.create_and_login('client1', 'client')

        res = self.client.post(
            '/projects/',
            {'title': 'Landing page', 'description': 'Build one', 'budget': 100},
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        res = self.client.get('/projects/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['title'], 'Landing page')

    def test_create_project_rejects_invalid_budget(self):
        self.create_and_login('client1', 'client')

        res = self.client.post(
            '/projects/',
            {'title': 'Landing page', 'description': 'Build one', 'budget': 0},
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class ProjectListPaginationTests(AuthenticatedAPITestCase):
    """Covers the ?skip=&limit= query params, including the 500-on-bad-input bug."""

    def setUp(self):
        self.client_user = self.create_and_login('client1', 'client')
        for i in range(3):
            Project.objects.create(
                title=f'Project {i}', description='desc', budget=100,
                owner=self.client_user,
            )

    def test_default_pagination(self):
        res = self.client.get('/projects/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 3)

    def test_limit_is_respected(self):
        res = self.client.get('/projects/?limit=2')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)

    def test_non_numeric_skip_returns_400_not_500(self):
        """
        Regression test: this used to raise an uncaught ValueError
        (int('abc')) and return a 500 instead of a clean validation error.
        """
        res = self.client.get('/projects/?skip=abc')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_numeric_limit_returns_400_not_500(self):
        res = self.client.get('/projects/?limit=xyz')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_negative_skip_returns_400(self):
        res = self.client.get('/projects/?skip=-1')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_search_filters_by_title(self):
        res = self.client.get('/projects/?search=Project 1')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['title'], 'Project 1')


class BidFlowTests(AuthenticatedAPITestCase):
    def setUp(self):
        self.client_user = self.create_and_login('client1', 'client')
        self.project = Project.objects.create(
            title='Landing page', description='Build one', budget=100,
            owner=self.client_user,
        )

    def test_owner_cannot_bid_on_own_project(self):
        res = self.client.post(
            f'/projects/{self.project.id}/bids/',
            {'price': 90, 'message': 'I will do it myself'},
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_freelancer_can_submit_bid(self):
        self.create_and_login('freelancer1', 'freelancer')

        res = self.client.post(
            f'/projects/{self.project.id}/bids/',
            {'price': 90, 'message': 'I can build this quickly'},
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Bid.objects.filter(project=self.project).count(), 1)

    def test_freelancer_cannot_bid_twice_on_same_project(self):
        self.create_and_login('freelancer1', 'freelancer')

        self.client.post(
            f'/projects/{self.project.id}/bids/',
            {'price': 90, 'message': 'First bid attempt'},
        )
        res = self.client.post(
            f'/projects/{self.project.id}/bids/',
            {'price': 95, 'message': 'Second bid attempt'},
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Bid.objects.filter(project=self.project).count(), 1)


class AcceptBidTests(AuthenticatedAPITestCase):
    def setUp(self):
        self.client_user = self.create_and_login('client1', 'client')
        self.project = Project.objects.create(
            title='Landing page', description='Build one', budget=100,
            owner=self.client_user,
        )
        self.freelancer1 = self.create_and_login('freelancer1', 'freelancer')
        self.bid1 = Bid.objects.create(
            price=90, message='pick me', project=self.project,
            freelancer=self.freelancer1,
        )
        self.freelancer2 = self.create_and_login('freelancer2', 'freelancer')
        self.bid2 = Bid.objects.create(
            price=80, message='pick me instead', project=self.project,
            freelancer=self.freelancer2,
        )
        # switch back to the project owner for the accept call
        self.login_as(self.client_user)

    def test_accept_bid_returns_200(self):
        """
        Regression test: accepting a bid previously returned 201 Created,
        which is wrong for an update (PATCH) on an existing resource.
        """
        res = self.client.patch(
            f'/projects/{self.project.id}/bids/{self.bid1.id}/accept/'
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_accept_bid_sets_winner_and_rejects_others(self):
        self.client.patch(
            f'/projects/{self.project.id}/bids/{self.bid1.id}/accept/'
        )
        self.project.refresh_from_db()
        self.bid1.refresh_from_db()
        self.bid2.refresh_from_db()

        self.assertEqual(self.project.winner_id, self.freelancer1.id)
        self.assertEqual(self.project.status, ProjectStatus.IN_PROGRESS)
        self.assertEqual(self.bid1.status, BidStatus.ACCEPTED)
        self.assertEqual(self.bid2.status, BidStatus.REJECTED)


class CancelProjectTests(AuthenticatedAPITestCase):
    def setUp(self):
        self.client_user = self.create_and_login('client1', 'client')
        self.project = Project.objects.create(
            title='Landing page', description='Build one', budget=100,
            owner=self.client_user,
        )
        self.freelancer = self.create_and_login('freelancer1', 'freelancer')
        self.bid = Bid.objects.create(
            price=90, message='pick me', project=self.project,
            freelancer=self.freelancer,
        )
        self.login_as(self.client_user)

    def test_cancel_rejects_open_bids_with_a_valid_status(self):
        """
        Regression test: cancelling a project used to set
        Bid.status = ProjectStatus.CANCELED ('canceled'), which isn't a
        valid BidStatus choice at all. It should be BidStatus.REJECTED.
        """
        res = self.client.patch(f'/projects/{self.project.id}/cancel/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.project.refresh_from_db()
        self.bid.refresh_from_db()
        self.assertEqual(self.project.status, ProjectStatus.CANCELED)
        self.assertEqual(self.bid.status, BidStatus.REJECTED)

    def test_cannot_cancel_already_canceled_project(self):
        self.client.patch(f'/projects/{self.project.id}/cancel/')
        res = self.client.patch(f'/projects/{self.project.id}/cancel/')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_cancel_in_progress_project(self):
        self.project.status = ProjectStatus.IN_PROGRESS
        self.project.save()
        res = self.client.patch(f'/projects/{self.project.id}/cancel/')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
