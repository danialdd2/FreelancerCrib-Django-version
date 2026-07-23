"""Tests for core.permissions.IsAdminRole."""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from rest_framework.test import APIRequestFactory

from core.enums import UserType
from core.permissions import IsAdminRole

User = get_user_model()


class IsAdminRoleTests(TestCase):
    def setUp(self):
        self.permission = IsAdminRole()
        self.factory = APIRequestFactory()
        self.request = self.factory.get('/admin/')

    def test_anonymous_user_denied(self):
        self.request.user = AnonymousUser()
        self.assertFalse(self.permission.has_permission(self.request, None))

    def test_regular_authenticated_user_denied(self):
        user = User.objects.create_user(
            username='client1', password='strongpass1', role=UserType.USER,
        )
        self.request.user = user
        self.assertFalse(self.permission.has_permission(self.request, None))

    def test_admin_user_allowed(self):
        admin = User.objects.create_user(
            username='admin1', password='strongpass1', role=UserType.ADMIN,
        )
        self.request.user = admin
        self.assertTrue(self.permission.has_permission(self.request, None))
