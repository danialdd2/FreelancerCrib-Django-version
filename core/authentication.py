"""
Custom DRF authentication backend.

Decodes the bearer JWT from the Authorization header and attaches the
matching User instance to request.user, giving every view direct access
to user.role, user.user_role, user.id, and related objects.
"""
import jwt
from django.contrib.auth import get_user_model
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework import authentication, exceptions

from core.jwt_utils import decode_access_token

User = get_user_model()


class JWTAuthentication(authentication.BaseAuthentication):
    keyword = 'Bearer'

    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '').strip()
        if not auth_header:
            return None  # no token provided -> let other checks handle it

        token = self._extract_token(auth_header)
        if token is None:
            return None  # doesn't look like our scheme -> not our problem

        try:
            payload = decode_access_token(token)
        except jwt.PyJWTError as exc:
            raise exceptions.AuthenticationFailed('could not validate user') from exc

        user_id = payload.get('id')
        username = payload.get('sub')
        if user_id is None or username is None:
            raise exceptions.AuthenticationFailed('could not validate user')

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist as exc:
            raise exceptions.AuthenticationFailed('could not validate user') from exc

        return (user, token)

    def _extract_token(self, auth_header):
        """
        Pull the raw JWT out of the Authorization header.
        """
        value = auth_header
        matched_once = False
        while value.lower().startswith(f'{self.keyword.lower()} '):
            value = value[len(self.keyword) + 1:].strip()
            matched_once = True

        if not matched_once:
            return None

        return value.strip('"\'')

    def authenticate_header(self, request):
        return self.keyword


class JWTAuthenticationScheme(OpenApiAuthenticationExtension):
    """
    Tells drf-spectacular how to represent JWTAuthentication in the OpenAPI
    schema.

     without this, drf-spectacular has no idea how a custom
    authentication class works, so it never emits a `securitySchems`
    entry - which is why Swager UI showed no "Authorize" button/lock icon
    at all, even after logging in there was nowhere to paste the token.
    This makes it show a standard "Bearer <token>" fild.
    """
    target_class = 'core.authentication.JWTAuthentication'
    name = 'jwtAuth'  # referenced by SPECTACULAR_SETTINGS.SECURITY, if set

    def get_security_definition(self, auto_schema):
        return {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT',
            'description': (
                '1) Call POST /auth/token/ with your username/password. '
                '2) Copy just the "access_token" value from the response '
                '(no quotes). 3) Paste ONLY that value here - do NOT type '
                'the word "Bearer" yourself, Swagger adds it for you '
                'automatically.'
            ),
        }
