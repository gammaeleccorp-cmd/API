from django.contrib import admin

from .models import Vehicle
from .services import deactivate_vehicle


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ("vin", "owner", "device", "is_active", "activated_at", "created_at")
    list_filter = ("is_active",)
    list_select_related = ("owner", "device")
    search_fields = ("vin", "owner__username", "owner__mobile", "owner__company_name", "device__serial")
    autocomplete_fields = ("owner",)
    # Activation needs the owner/device checks and a device token, so it only happens through the API.
    readonly_fields = ("device", "is_active", "activated_at", "created_at")
    actions = ["force_deactivate"]

    @admin.action(description="Force deactivate (unbind owner and device)")
    def force_deactivate(self, request, queryset):
        count = 0
        for vehicle in queryset:
            deactivate_vehicle(vehicle)
            count += 1
        self.message_user(request, f"Deactivated {count} vehicle(s).")
