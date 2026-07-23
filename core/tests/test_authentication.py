"""Tests for core.authentication.JWTAuthentication and core.jwt_utils."""
from datetime import timedelta

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from core.authentication import JWTAuthentication
from core.jwt_utils import create_access_token, decode_access_token

User = get_user_model()


class JwtUtilsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='jwtuser', password='strongpass1', user_role='client',
        )

    def test_create_and_decode_round_trip(self):
        token = create_access_token(self.user)
        payload = decode_access_token(token)
        self.assertEqual(payload['sub'], self.user.username)
        self.assertEqual(payload['id'], self.user.id)
        self.assertEqual(payload['role'], self.user.role)

    def test_expired_token_fails_to_decode(self):
        token = create_access_token(self.user, expires_delta=timedelta(seconds=-1))
        with self.assertRaises(jwt.PyJWTError):
            decode_access_token(token)

    def test_token_signed_with_wrong_key_fails_to_decode(self):
        bad_token = jwt.encode(
            {'sub': self.user.username, 'id': self.user.id},
            'a-completely-different-secret',
            algorithm=settings.JWT_ALGORITHM,
        )
        with self.assertRaises(jwt.PyJWTError):
            decode_access_token(bad_token)


class JWTAuthenticationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='jwtuser', password='strongpass1', user_role='client',
        )
        self.auth = JWTAuthentication()
        self.factory = APIRequestFactory()

    def test_no_header_returns_none(self):
        request = self.factory.get('/user/me/')
        self.assertIsNone(self.auth.authenticate(request))

    def test_non_bearer_scheme_returns_none(self):
        request = self.factory.get('/user/me/', HTTP_AUTHORIZATION='Token abc123')
        self.assertIsNone(self.auth.authenticate(request))

    def test_valid_token_returns_user(self):
        token = create_access_token(self.user)
        request = self.factory.get('/user/me/', HTTP_AUTHORIZATION=f'Bearer {token}')
        user, returned_token = self.auth.authenticate(request)
        self.assertEqual(user, self.user)
        self.assertEqual(returned_token, token)

    def test_token_for_deleted_user_is_rejected(self):
        token = create_access_token(self.user)
        self.user.delete()
        request = self.factory.get('/user/me/', HTTP_AUTHORIZATION=f'Bearer {token}')
        from rest_framework.exceptions import AuthenticationFailed
        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate(request)

    def test_doubled_bearer_prefix_still_authenticates(self):
        """
        Regression test: Swagger's "Authorize" dialog for an http/bearer
        scheme already prepends "Bearer " to whatever's typed in. Typing
        "Bearer <token>" there too produces a header of
        "Bearer Bearer <token>" - this used to always fail with
        AuthenticationFailed even for an otherwise-valid token.
        """
        token = create_access_token(self.user)
        request = self.factory.get(
            '/user/me/', HTTP_AUTHORIZATION=f'Bearer Bearer {token}'
        )
        user, returned_token = self.auth.authenticate(request)
        self.assertEqual(user, self.user)
        self.assertEqual(returned_token, token)

    def test_lowercase_bearer_keyword_is_accepted(self):
        token = create_access_token(self.user)
        request = self.factory.get('/user/me/', HTTP_AUTHORIZATION=f'bearer {token}')
        user, returned_token = self.auth.authenticate(request)
        self.assertEqual(user, self.user)

    def test_stray_quotes_around_token_are_stripped(self):
        """
        Regression test: pasting the raw JSON value of "access_token"
        (quotes and all) instead of just its contents used to fail to
        decode.
        """
        token = create_access_token(self.user)
        request = self.factory.get(
            '/user/me/', HTTP_AUTHORIZATION=f'Bearer "{token}"'
        )
        user, returned_token = self.auth.authenticate(request)
        self.assertEqual(user, self.user)
        self.assertEqual(returned_token, token)
