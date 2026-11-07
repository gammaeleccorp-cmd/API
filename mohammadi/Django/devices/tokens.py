"""Device tokens: long-lived JWTs without `exp`, revocable through Device.token_version."""
import jwt
from django.conf import settings

ALGORITHM = "HS256"
TOKEN_TYPE = "device"


def create_device_token(device) -> str:
    payload = {
        "token_type": TOKEN_TYPE,
        "role": "device",
        "sub": str(device.id),
        "serial": device.serial,
        "token_version": device.token_version,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_device_token(token: str) -> dict:
    claims = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[ALGORITHM],
        options={"require": ["sub", "token_version"]},
    )
    if claims.get("token_type") != TOKEN_TYPE or claims.get("role") != "device":
        raise jwt.InvalidTokenError("Not a device token")
    return claims
