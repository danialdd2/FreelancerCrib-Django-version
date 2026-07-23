"""
Reusable DRF permission classes.

Used to restrict admin-only endpoints to users with the admin role.
"""
from rest_framework.permissions import BasePermission

from core.enums import UserType


class IsAdminRole(BasePermission):
    """Mirrors the admin-role check used in the admin router."""
    message = 'Admin access required'

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == UserType.ADMIN
        )
