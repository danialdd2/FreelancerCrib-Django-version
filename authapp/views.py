"""Login view that exchanges credentials for a JWT."""
from django.contrib.auth import authenticate
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.jwt_utils import create_access_token
from core.serializers import DetailResponseSerializer

from .serializers import LoginSerializer, TokenSerializer


class LoginView(APIView):
    """
    POST /auth/token/

    Django's authenticate() checks the submitted password against the
    stored hash for us.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['auth'],
        request=LoginSerializer,
        responses={
            200: TokenSerializer,
            401: DetailResponseSerializer,
        },
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            request,
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password'],
        )
        if user is None:
            return Response(
                {'detail': 'could not validate user'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        token = create_access_token(user)
        return Response({'access_token': token, 'token_type': 'bearer'})
