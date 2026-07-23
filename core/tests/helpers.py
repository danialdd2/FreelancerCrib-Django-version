"""
Shared test helpers.

Not a test module itself (no Test* classes here), just a base class other
apps' test suites import from, so login/token boilerplate isn't copy-pasted
in every file.
"""
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

User = get_user_model()


class AuthenticatedAPITestCase(APITestCase):
    """Base class that logs a user in and attaches the JWT to self.client."""

    def create_and_login(self, username, user_role, **extra):
        user = User.objects.create_user(
            username=username, password='strongpass1', user_role=user_role,
            **extra,
        )
        return self.login_as(user)

    def login_as(self, user):
        """Attach a JWT for an *already-created* user, without creating a
        new one. Use this to switch self.client back to a user created
        earlier in the same test/setUp - calling create_and_login() again
        with that username would try to INSERT a duplicate row."""
        res = self.client.post(
            '/auth/token/', {'username': user.username, 'password': 'strongpass1'}
        )
        token = res.data['access_token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        return user
