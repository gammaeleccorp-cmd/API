from datetime import timedelta

from django.conf import settings
from django.utils import timezone


def is_device_online(device) -> bool:
    heartbeat = device.last_heartbeat_at
    if heartbeat is None:
        return False
    return (timezone.now() - heartbeat) <= timedelta(seconds=settings.DEVICE_OFFLINE_AFTER_SECONDS)
