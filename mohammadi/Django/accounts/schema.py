"""Describe the JWT scheme to Swagger so the Authorize button logs in with username + password."""
from drf_spectacular.extensions import OpenApiAuthenticationExtension


class AppJWTAuthScheme(OpenApiAuthenticationExtension):
    target_class = "accounts.authentication.AppJWTAuthentication"
    name = "jwtAuth"

    def get_security_definition(self, auto_schema):
        return {
            "type": "oauth2",
            "flows": {"password": {"tokenUrl": "/api/auth/login/", "scopes": {}}},
        }