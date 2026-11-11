
from django.db import models


class TelemetryRecord(models.Model):
    device = models.ForeignKey(
        "devices.Device",
        on_delete=models.CASCADE,
        related_name="telemetry_records"
    )

    data = models.JSONField()
    recorded_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Telemetry - {self.device.serial_number}"
