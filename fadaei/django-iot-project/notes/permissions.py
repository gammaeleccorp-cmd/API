from rest_framework.permissions import BasePermission


class IsNoteOwner(BasePermission):
    message = "You do not have permission to access this note."

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user
