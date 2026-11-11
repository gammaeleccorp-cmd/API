
from django.contrib import admin
from .models import Vehicle


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "brand", "model", "vin", "owner", "created_at")
    search_fields = ("name", "brand", "model", "vin")
    list_filter = ("brand", "created_at")
