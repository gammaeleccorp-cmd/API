from django.conf import settings
from django.db import models


class Vehicle(models.Model):
    vin = models.CharField(max_length=17, unique=True)
    # Owner is set when the vehicle is registered/activated and cleared on deactivation.
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="vehicles"
    )
    device = models.OneToOneField(
        "devices.Device", null=True, blank=True, on_delete=models.SET_NULL, related_name="vehicle"
    )
    is_active = models.BooleanField(default=False)
    activated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.vin
