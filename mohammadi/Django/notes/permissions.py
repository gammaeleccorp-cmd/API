from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    """Allow access only to the owner of the object (object-level; does not protect list)."""

    def has_object_permission(self, request, view, obj):
        return obj.owner_id == request.user.id
