from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class Device(models.Model):
    serial = models.CharField(max_length=100, unique=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="devices")
    last_heartbeat_at = models.DateTimeField(null=True, blank=True)
    # Bumping this number invalidates every device token issued before.
    token_version = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.serial


class DeviceCommand(models.Model):
    class CommandType(models.TextChoices):
        IGNITE = "ignite"
        SWITCH_OFF = "switch_off"
        LOCATE = "locate"

    class Status(models.TextChoices):
        PENDING = "pending"
        DELIVERED = "delivered"
        ACKNOWLEDGED = "acknowledged"

    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name="commands")
    command_type = models.CharField(max_length=20, choices=CommandType.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["device", "status"])]
        constraints = [
            # Only one identical command may be pending/delivered per device at a time.
            models.UniqueConstraint(
                fields=["device", "command_type"],
                condition=Q(status__in=["pending", "delivered"]),
                name="unique_active_command_per_device_type",
            )
        ]

    def clean(self):
        super().clean()
        if self._state.adding and self.device_id and self.command_type:
            exists = DeviceCommand.objects.filter(
                device_id=self.device_id,
                command_type=self.command_type,
                status__in=[self.Status.PENDING, self.Status.DELIVERED],
            ).exists()
            if exists:
                raise ValidationError("An identical command is already pending or in progress.")

    def __str__(self):
        return f"{self.command_type} -> {self.device_id} ({self.status})"
