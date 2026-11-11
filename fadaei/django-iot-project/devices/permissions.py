from rest_framework.permissions import BasePermission


class IsVehicleOwner(BasePermission):
    message = "You do not have permission to access this vehicle."

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user
