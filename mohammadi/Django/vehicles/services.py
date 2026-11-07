from django.db import transaction
from django.utils import timezone

from accounts.exceptions import Conflict
from devices.models import Device
from devices.tokens import create_device_token

from .models import Vehicle


def activate_vehicle(vehicle, device, owner):
    """
    Atomically bind `device` to `vehicle` for `owner` and mark the vehicle active.
    Returns the vehicle with a transient `device_token` attribute (issued only here).
    """
    with transaction.atomic():
        device = Device.objects.select_for_update().get(pk=device.pk)
        vehicle = Vehicle.objects.select_for_update().get(pk=vehicle.pk)
        if vehicle.is_active:
            raise Conflict("Vehicle is already active")
        if Vehicle.objects.filter(device=device, is_active=True).exclude(pk=vehicle.pk).exists():
            raise Conflict("Device is already active on another vehicle")
        # Free the device from any inactive vehicle that still points at it.
        Vehicle.objects.filter(device=device).exclude(pk=vehicle.pk).update(device=None)
        vehicle.owner = owner
        vehicle.device = device
        vehicle.is_active = True
        vehicle.activated_at = timezone.now()
        vehicle.save()
    vehicle.device_token = create_device_token(device)
    return vehicle


def deactivate_vehicle(vehicle):
    vehicle.owner = None
    vehicle.device = None
    vehicle.is_active = False
    vehicle.save()
    return vehicle
