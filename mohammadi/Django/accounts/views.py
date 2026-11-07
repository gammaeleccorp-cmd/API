from django.db import IntegrityError, transaction
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .exceptions import Conflict
from .models import User
from .permissions import IsAccount
from .serializers import (
    LoginResponseSerializer,
    LoginSerializer,
    LogoutSerializer,
    RegisterSerializer,
    UserSerializer,
)


class PublicView(APIView):

    authentication_classes = []
    permission_classes = [AllowAny]

    def get_authenticate_header(self, request):
        return "Bearer"


class RegisterView(PublicView):
    @extend_schema(request=RegisterSerializer, responses={201: UserSerializer})
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if User.objects.filter(mobile=data["mobile"]).exists():
            raise Conflict("Mobile already registered")
        if User.objects.filter(national_id=data["national_id"]).exists():
            raise Conflict("National ID already registered")
        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=data["mobile"],
                    mobile=data["mobile"],
                    national_id=data["national_id"],
                    password=data["password"],
                )
        except IntegrityError:
            raise Conflict("Mobile or national ID already registered")
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer

    @extend_schema(responses=LoginResponseSerializer)
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class RefreshView(TokenRefreshView):
    """Rotates the refresh token: the old one is blacklisted and a new pair is returned."""


class LogoutView(PublicView):
    @extend_schema(request=LogoutSerializer, responses={204: None})
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            RefreshToken(serializer.validated_data["refresh"]).blacklist()
        except TokenError:
            pass  # already invalid: logging out is idempotent
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = [IsAccount]

    @extend_schema(responses=UserSerializer)
    def get(self, request):
        return Response(UserSerializer(request.user).data)
