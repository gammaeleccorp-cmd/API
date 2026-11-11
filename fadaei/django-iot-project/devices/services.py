
from django.db import transaction

from devices.models import Device
from vehicles.models import Vehicle


@transaction.atomic
def activate_device(
    *,
    user,
    serial_number,
    name,
    brand,
    model,
    vin
):
    # 1. Find and lock the device
    try:
        device = Device.objects.select_for_update().get(
            serial_number=serial_number
        )
    except Device.DoesNotExist:
        raise ValueError("Device not found.")

    # 2. Check whether the device was already activated
    if device.vehicle is not None:
        raise ValueError("This device has already been activated.")

    # 3. Create a vehicle for the authenticated user
    vehicle = Vehicle.objects.create(
        owner=user,
        name=name,
        brand=brand,
        model=model,
        vin=vin
    )

    # 4. Connect the device to the vehicle
    device.vehicle = vehicle
    device.save(update_fields=["vehicle"])

    # 5. Return the created vehicle
    return vehicle
