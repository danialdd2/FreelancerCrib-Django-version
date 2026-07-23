"""Tests for the notifications endpoints."""
from rest_framework import status

from core.models import Bid, Notification, Project
from core.tests.helpers import AuthenticatedAPITestCase


class NotificationListTests(AuthenticatedAPITestCase):
    def test_returns_404_when_no_notifications(self):
        self.create_and_login('client1', 'client')
        res = self.client.get('/notifications/')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_bid_submission_creates_notification_for_owner(self):
        owner = self.create_and_login('client1', 'client')
        project = Project.objects.create(
            title='Landing page', description='Build one', budget=100,
            owner=owner,
        )
        self.create_and_login('freelancer1', 'freelancer')
        self.client.post(
            f'/projects/{project.id}/bids/', {'price': 90, 'message': 'pick me'}
        )

        self.assertEqual(Notification.objects.filter(user=owner).count(), 1)

        self.login_as(owner)
        res = self.client.get('/notifications/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)


class UnreadNotificationTests(AuthenticatedAPITestCase):
    def setUp(self):
        self.user = self.create_and_login('client1', 'client')
        self.n1 = Notification.objects.create(
            user=self.user, title='First', message='msg', type='new_bid',
        )
        self.n2 = Notification.objects.create(
            user=self.user, title='Second', message='msg', type='new_bid',
        )

    def test_unread_count_returns_a_json_object(self):
        """
        Regression test: this endpoint used to return a bare integer
        (Response(count)) instead of a JSON object.
        """
        res = self.client.get('/notifications/unread-count/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {'count': 2})

    def test_unread_list_returns_only_unread(self):
        self.n1.is_read = True
        self.n1.save()

        res = self.client.get('/notifications/unread/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)

    def test_mark_single_notification_read(self):
        res = self.client.patch(f'/notifications/{self.n1.id}/read/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.n1.refresh_from_db()
        self.assertTrue(self.n1.is_read)

    def test_mark_all_notifications_read(self):
        res = self.client.patch('/notifications/read-all/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {'message': 'messages read successfully'})

        self.n1.refresh_from_db()
        self.n2.refresh_from_db()
        self.assertTrue(self.n1.is_read)
        self.assertTrue(self.n2.is_read)

    def test_delete_notification(self):
        res = self.client.delete(f'/notifications/{self.n1.id}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {'message': 'message deleted successfully'})
        self.assertFalse(Notification.objects.filter(id=self.n1.id).exists())

    def test_cannot_read_or_delete_someone_elses_notification(self):
        self.create_and_login('other_user', 'client')
        res = self.client.patch(f'/notifications/{self.n1.id}/read/')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

        res = self.client.delete(f'/notifications/{self.n1.id}/')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
