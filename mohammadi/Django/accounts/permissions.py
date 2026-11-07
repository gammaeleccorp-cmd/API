from rest_framework.permissions import BasePermission

DEVICE_ROLE = "device"


def role_required(*roles):
    """Build a permission class that allows only the given roles (user / company / device)."""

    class _RolePermission(BasePermission):
        message = "Not enough permissions"

        def has_permission(self, request, view):
            principal = request.user
            if principal is None or not getattr(principal, "is_authenticated", False):
                return False
            role = getattr(principal, "role", None)
            if role not in roles:
                return False
            if role == DEVICE_ROLE:
                # A revoked device token is authenticated but not allowed (403).
                return principal.is_token_current
            return True

    _RolePermission.__name__ = "Is_" + "_or_".join(roles)
    return _RolePermission


IsUser = role_required("user")
IsCompany = role_required("company")
IsDevice = role_required("device")
IsAccount = role_required("user", "company")  # any human account (not a device)
