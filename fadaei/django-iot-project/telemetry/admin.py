
from django.contrib import admin
from .models import TelemetryRecord


@admin.register(TelemetryRecord)
class TelemetryRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "device", "recorded_at", "created_at")
    search_fields = ("device__serial_number",)
    list_filter = ("recorded_at", "created_at")
    readonly_fields = ("device", "data", "recorded_at", "created_at")

