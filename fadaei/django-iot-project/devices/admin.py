
from django.contrib import admin
from .models import Device


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ("id", "serial_number", "vehicle", "created_at")
    search_fields = ("serial_number",)
    list_filter = ("created_at",)
