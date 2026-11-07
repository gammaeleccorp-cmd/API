"""JWT authentication for user/company accounts (simplejwt) and for device tokens."""
from dataclasses import dataclass
from typing import Any

import jwt
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication

from .permissions import DEVICE_ROLE


@dataclass
class DevicePrincipal:
    """Stands in for request.user when a request carries a device token."""

    device: Any
    claims: dict
    role: str = DEVICE_ROLE
    is_authenticated: bool = True
    is_anonymous: bool = False

    @property
    def is_token_current(self) -> bool:
        return self.claims.get("token_version") == self.device.token_version


class AppJWTAuthentication(JWTAuthentication):
    """
    * Device tokens (role=device) are verified with PyJWT and resolve to a DevicePrincipal.
    * Everything else goes through simplejwt and resolves to a User.
    * Staff accounts belong to the admin panel and cannot authenticate against the API.
    """

    def authenticate(self, request):
        header = self.get_header(request)
        if header is None:
            return None
        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None
        if self._looks_like_device_token(raw_token):
            return self._authenticate_device(raw_token), raw_token
        return super().authenticate(request)

    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        if user.is_staff or user.is_superuser:
            raise AuthenticationFailed("Staff accounts can only use the admin panel.", code="staff_not_allowed")
        return user

    @staticmethod
    def _looks_like_device_token(raw_token):
        try:
            claims = jwt.decode(raw_token, options={"verify_signature": False})
        except jwt.PyJWTError:
            return False
        return claims.get("role") == DEVICE_ROLE

    @staticmethod
    def _authenticate_device(raw_token):
        from devices.models import Device
        from devices.tokens import decode_device_token

        try:
            claims = decode_device_token(raw_token)
            device_id = int(claims["sub"])
        except (jwt.PyJWTError, KeyError, ValueError):
            raise AuthenticationFailed("Could not validate credentials")
        device = Device.objects.filter(pk=device_id).first()
        if device is None:
            raise AuthenticationFailed("Could not validate credentials")
        return DevicePrincipal(device=device, claims=claims)
