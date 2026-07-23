"""Tests for submitting, listing, editing, and deleting bids."""
from rest_framework import status

from core.enums import BidStatus, ProjectStatus
from core.models import Bid, Project
from core.tests.helpers import AuthenticatedAPITestCase


class SubmitBidTests(AuthenticatedAPITestCase):
    def setUp(self):
        self.client_user = self.create_and_login('client1', 'client')
        self.project = Project.objects.create(
            title='Landing page', description='Build one', budget=100,
            owner=self.client_user,
        )

    def test_cannot_bid_on_canceled_project(self):
        self.project.status = ProjectStatus.CANCELED
        self.project.save()
        self.create_and_login('freelancer1', 'freelancer')

        res = self.client.post(
            f'/projects/{self.project.id}/bids/',
            {'price': 90, 'message': 'still interested'},
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_bid_on_completed_project(self):
        self.project.status = ProjectStatus.COMPLETED
        self.project.save()
        self.create_and_login('freelancer1', 'freelancer')

        res = self.client.post(
            f'/projects/{self.project.id}/bids/',
            {'price': 90, 'message': 'still interested'},
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bid_on_missing_project_returns_404(self):
        self.create_and_login('freelancer1', 'freelancer')
        res = self.client.post(
            '/projects/999999/bids/', {'price': 90, 'message': 'hello there'}
        )
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_bid_message_too_short_is_rejected(self):
        self.create_and_login('freelancer1', 'freelancer')
        res = self.client.post(
            f'/projects/{self.project.id}/bids/', {'price': 90, 'message': 'hi'}
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class ListBidsTests(AuthenticatedAPITestCase):
    def setUp(self):
        self.client_user = self.create_and_login('client1', 'client')
        self.project = Project.objects.create(
            title='Landing page', description='Build one', budget=100,
            owner=self.client_user,
        )

    def test_list_bids_returns_404_when_empty(self):
        res = self.client.get(f'/projects/{self.project.id}/bids/')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_non_owner_cannot_list_bids(self):
        freelancer = self.create_and_login('freelancer1', 'freelancer')
        Bid.objects.create(
            price=90, message='pick me please', project=self.project,
            freelancer=freelancer,
        )
        # freelancer1 is logged in now, not the project owner
        res = self.client.get(f'/projects/{self.project.id}/bids/')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_owner_can_list_bids(self):
        freelancer = self.create_and_login('freelancer1', 'freelancer')
        Bid.objects.create(
            price=90, message='pick me please', project=self.project,
            freelancer=freelancer,
        )
        self.login_as(self.client_user)

        res = self.client.get(f'/projects/{self.project.id}/bids/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)


class MyBidsTests(AuthenticatedAPITestCase):
    def test_returns_404_when_no_bids(self):
        self.create_and_login('freelancer1', 'freelancer')
        res = self.client.get('/users/me/bids/')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_returns_own_bids_only(self):
        client_user = self.create_and_login('client1', 'client')
        project = Project.objects.create(
            title='Landing page', description='Build one', budget=100,
            owner=client_user,
        )
        freelancer1 = self.create_and_login('freelancer1', 'freelancer')
        Bid.objects.create(
            price=90, message='pick me please', project=project,
            freelancer=freelancer1,
        )
        freelancer2 = self.create_and_login('freelancer2', 'freelancer')
        Bid.objects.create(
            price=80, message='pick me instead', project=project,
            freelancer=freelancer2,
        )

        # freelancer2 is currently logged in
        res = self.client.get('/users/me/bids/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['price'], 80)


class BidDetailTests(AuthenticatedAPITestCase):
    def setUp(self):
        self.client_user = self.create_and_login('client1', 'client')
        self.project = Project.objects.create(
            title='Landing page', description='Build one', budget=100,
            owner=self.client_user,
        )
        self.freelancer = self.create_and_login('freelancer1', 'freelancer')
        self.bid = Bid.objects.create(
            price=90, message='pick me please', project=self.project,
            freelancer=self.freelancer,
        )

    def test_owner_of_bid_can_update_pending_bid(self):
        res = self.client.put(
            f'/bids/{self.bid.id}/', {'price': 95, 'message': 'updated offer'}
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.bid.refresh_from_db()
        self.assertEqual(self.bid.price, 95)

    def test_cannot_update_someone_elses_bid(self):
        self.create_and_login('freelancer2', 'freelancer')
        res = self.client.put(
            f'/bids/{self.bid.id}/', {'price': 95, 'message': 'sneaky update'}
        )
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_update_non_pending_bid(self):
        """
        Regression test: a bid could previously be edited even after it
        had already been accepted or rejected.
        """
        self.bid.status = BidStatus.ACCEPTED
        self.bid.save()
        res = self.client.put(
            f'/bids/{self.bid.id}/', {'price': 95, 'message': 'too late now'}
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_owner_of_bid_can_delete_pending_bid(self):
        res = self.client.delete(f'/bids/{self.bid.id}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertFalse(Bid.objects.filter(id=self.bid.id).exists())

    def test_cannot_delete_non_pending_bid(self):
        """Same regression as above, but for DELETE."""
        self.bid.status = BidStatus.REJECTED
        self.bid.save()
        res = self.client.delete(f'/bids/{self.bid.id}/')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(Bid.objects.filter(id=self.bid.id).exists())
