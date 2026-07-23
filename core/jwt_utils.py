"""
JWT helpers.

Encode and decode signed JWTs carrying the user's id, username,
and role claims.
"""
from datetime import datetime, timedelta, timezone

import jwt
from django.conf import settings


def create_access_token(user, expires_delta: timedelta = None) -> str:
    """Build a signed JWT for the given user.

    Embeds sub (username), id, role, and user_role claims.
    """
    expires_delta = expires_delta or settings.JWT_ACCESS_TOKEN_EXPIRE
    expires = datetime.now(timezone.utc) + expires_delta
    payload = {
        'sub': user.username,
        'id': user.id,
        'role': user.role,
        'user_role': user.user_role,
        'exp': expires,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT, raising jwt.PyJWTError on failure."""
    return jwt.decode(
        token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
    )
