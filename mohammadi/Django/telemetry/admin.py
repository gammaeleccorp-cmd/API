from django.contrib import admin

from .models import Telemetry


@admin.register(Telemetry)
class TelemetryAdmin(admin.ModelAdmin):
    """Read-only browser for telemetry points (they are written by devices only)."""

    list_display = ("id", "vehicle", "device", "latitude", "longitude", "speed", "recorded_at")
    list_filter = ("recorded_at",)
    list_select_related = ("vehicle", "device")
    search_fields = ("vehicle__vin", "device__serial")
    date_hierarchy = "recorded_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
