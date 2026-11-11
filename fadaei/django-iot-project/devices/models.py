
from django.db import models


class Device(models.Model):
    vehicle = models.OneToOneField(
        "vehicles.Vehicle",
        on_delete=models.CASCADE,
        related_name="device",
        null=True,
        blank=True
    )

    serial_number = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.serial_number
