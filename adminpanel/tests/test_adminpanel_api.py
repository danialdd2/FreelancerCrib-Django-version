"""Tests for the admin-only user management endpoints."""
from rest_framework import status

from core.enums import UserType
from core.tests.helpers import AuthenticatedAPITestCase


class AdminAccessControlTests(AuthenticatedAPITestCase):
    def test_regular_user_cannot_list_users(self):
        self.create_and_login('client1', 'client')
        res = self.client.get('/admin/users/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_user_cannot_list_users(self):
        # No credentials at all -> DRF reports 401 (not authenticated),
        # reserving 403 for "authenticated but not permitted".
        res = self.client.get('/admin/users/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_can_list_users(self):
        self.create_and_login('client1', 'client')
        self.create_and_login('admin1', 'client', role=UserType.ADMIN)

        res = self.client.get('/admin/users/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        usernames = [u['username'] for u in res.data]
        self.assertIn('client1', usernames)
        self.assertIn('admin1', usernames)


class PromoteToAdminTests(AuthenticatedAPITestCase):
    def setUp(self):
        self.target = self.create_and_login('client1', 'client')
        self.admin = self.create_and_login('admin1', 'client', role=UserType.ADMIN)

    def test_promote_user_to_admin(self):
        res = self.client.patch(f'/admin/users/{self.target.id}/role/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.target.refresh_from_db()
        self.assertEqual(self.target.role, UserType.ADMIN)

    def test_promote_already_admin_user_returns_400(self):
        res = self.client.patch(f'/admin/users/{self.admin.id}/role/')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_promote_missing_user_returns_404(self):
        res = self.client.patch('/admin/users/999999/role/')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_non_admin_cannot_promote(self):
        self.create_and_login('regular1', 'client')
        res = self.client.patch(f'/admin/users/{self.target.id}/role/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class ListAdminsTests(AuthenticatedAPITestCase):
    def test_only_returns_admin_role_users(self):
        self.create_and_login('client1', 'client')
        admin = self.create_and_login('admin1', 'client', role=UserType.ADMIN)

        res = self.client.get('/admin/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        usernames = [u['username'] for u in res.data]
        self.assertEqual(usernames, [admin.username])
