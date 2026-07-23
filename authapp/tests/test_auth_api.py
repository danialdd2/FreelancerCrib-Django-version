"""Extra edge-case coverage for POST /auth/token/ (happy-path cases live
in users/tests/test_users_api.py::LoginTests)."""
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class TokenEndpointValidationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='authuser', password='strongpass1', user_role='client'
        )

    def test_missing_username_returns_400(self):
        res = self.client.post('/auth/token/', {'password': 'strongpass1'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_password_returns_400(self):
        res = self.client.post('/auth/token/', {'username': 'authuser'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_inactive_user_cannot_log_in(self):
        self.user.is_active = False
        self.user.save()
        res = self.client.post(
            '/auth/token/', {'username': 'authuser', 'password': 'strongpass1'}
        )
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_is_accepted_by_protected_endpoint(self):
        res = self.client.post(
            '/auth/token/', {'username': 'authuser', 'password': 'strongpass1'}
        )
        token = res.data['access_token']

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        res = self.client.get('/user/me/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_malformed_bearer_token_is_rejected(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer not-a-real-token')
        res = self.client.get('/user/me/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
