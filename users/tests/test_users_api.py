"""Tests for user registration, login, and profile endpoints."""
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from core.tests.helpers import AuthenticatedAPITestCase

User = get_user_model()


class RegisterUserTests(APITestCase):
    def test_register_user_success(self):
        payload = {
            'username': 'newuser1',
            'email': 'newuser1@example.com',
            'full_name': 'New User',
            'password': 'strongpass1',
            'user_role': 'client',
        }
        res = self.client.post('/user/', payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username='newuser1')
        self.assertTrue(user.check_password('strongpass1'))

    def test_register_user_password_too_short(self):
        payload = {
            'username': 'newuser2',
            'email': 'newuser2@example.com',
            'full_name': 'New User',
            'password': 'short',
            'user_role': 'client',
        }
        res = self.client.post('/user/', payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username='newuser2').exists())

    def test_register_user_duplicate_username_rejected(self):
        User.objects.create_user(username='dupeuser', password='strongpass1')
        payload = {
            'username': 'dupeuser',
            'email': 'dupe2@example.com',
            'full_name': 'Dupe User',
            'password': 'strongpass1',
            'user_role': 'client',
        }
        res = self.client.post('/user/', payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class LoginTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='loginuser', password='strongpass1', user_role='client'
        )

    def test_login_with_correct_credentials_returns_token(self):
        res = self.client.post(
            '/auth/token/',
            {'username': 'loginuser', 'password': 'strongpass1'},
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', res.data)
        self.assertEqual(res.data['token_type'], 'bearer')

    def test_login_with_wrong_password_fails(self):
        res = self.client.post(
            '/auth/token/',
            {'username': 'loginuser', 'password': 'wrongpass'},
        )

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_with_unknown_username_fails(self):
        res = self.client.post(
            '/auth/token/',
            {'username': 'nosuchuser', 'password': 'whatever1'},
        )
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class MeEndpointTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='profileuser', password='strongpass1',
            email='profile@example.com', full_name='Profile User',
            user_role='freelancer',
        )

    def _authenticate(self):
        res = self.client.post(
            '/auth/token/',
            {'username': 'profileuser', 'password': 'strongpass1'},
        )
        token = res.data['access_token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_me_requires_authentication(self):
        res = self.client.get('/user/me/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_returns_own_profile(self):
        self._authenticate()
        res = self.client.get('/user/me/')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['username'], 'profileuser')

    def test_me_update_changes_profile(self):
        self._authenticate()
        res = self.client.put(
            '/user/me/',
            {
                'username': 'profileuser',
                'email': 'newemail@example.com',
                'full_name': 'Updated Name',
            },
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'newemail@example.com')


class UserDetailTests(AuthenticatedAPITestCase):
    def test_user_detail_requires_auth(self):
        res = self.client.get('/user/1/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_detail_returns_public_profile(self):
        target = User.objects.create_user(
            username='publicuser', password='strongpass1', full_name='Public User',
        )
        self.create_and_login('viewer1', 'client')

        res = self.client.get(f'/user/{target.id}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['username'], 'publicuser')
        self.assertNotIn('email', res.data)  # public serializer excludes it

    def test_unknown_user_id_returns_404_not_401(self):
        """
        Regression test: looking up a non-existent user id used to return
        401 Unauthorized even though the caller was authenticated, which
        incorrectly implied the *caller's* token was invalid.
        """
        self.create_and_login('viewer1', 'client')

        res = self.client.get('/user/999999/')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
