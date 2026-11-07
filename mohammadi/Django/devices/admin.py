from django.contrib import admin
from django.db.models import F

from .models import Device, DeviceCommand
from .services import is_device_online


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ("serial", "owner", "is_online", "last_heartbeat_at", "token_version", "created_at")
    list_select_related = ("owner",)
    search_fields = ("serial", "owner__username", "owner__mobile", "owner__company_name")
    autocomplete_fields = ("owner",)
    readonly_fields = ("last_heartbeat_at", "token_version", "created_at")
    actions = ["revoke_tokens"]

    @admin.display(boolean=True, description="Online")
    def is_online(self, obj):
        return is_device_online(obj)

    @admin.action(description="Revoke device token (invalidates the current token)")
    def revoke_tokens(self, request, queryset):
        count = queryset.update(token_version=F("token_version") + 1)
        self.message_user(request, f"Revoked the token of {count} device(s).")


@admin.register(DeviceCommand)
class DeviceCommandAdmin(admin.ModelAdmin):
    """Staff send commands here: add a command, the device picks it up on its next poll."""

    list_display = ("id", "device", "command_type", "status", "issued_by", "created_at")
    list_filter = ("status", "command_type")
    search_fields = ("device__serial",)
    list_select_related = ("device", "issued_by")
    autocomplete_fields = ("device",)

    def get_fields(self, request, obj=None):
        if obj:
            return ("device", "command_type", "status", "issued_by", "created_at", "delivered_at", "acknowledged_at")
        return ("device", "command_type")

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ("device", "command_type", "status", "issued_by", "created_at", "delivered_at", "acknowledged_at")
        return ()

    def save_model(self, request, obj, form, change):
        if not change:
            obj.issued_by = request.user
        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        return False
