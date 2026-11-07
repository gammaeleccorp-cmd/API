from django.db import models


class Telemetry(models.Model):
    device = models.ForeignKey("devices.Device", on_delete=models.CASCADE, related_name="telemetry")
    vehicle = models.ForeignKey("vehicles.Vehicle", on_delete=models.CASCADE, related_name="telemetry")
    latitude = models.FloatField()
    longitude = models.FloatField()
    speed = models.FloatField(null=True, blank=True)
    rpm = models.FloatField(null=True, blank=True)
    fuel_level = models.FloatField(null=True, blank=True)
    recorded_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "telemetry"
        indexes = [models.Index(fields=["vehicle", "-recorded_at"])]

    def __str__(self):
        return f"{self.vehicle_id} @ {self.recorded_at:%Y-%m-%d %H:%M:%S}"
