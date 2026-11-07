from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.exceptions import Conflict
from accounts.permissions import IsAccount, IsCompany, IsDevice, IsUser

from .models import Device, DeviceCommand
from .serializers import (
    CommandCreateSerializer,
    CommandSerializer,
    DeviceCreateSerializer,
    DeviceSerializer,
    HealthSerializer,
    MyDeviceSerializer,
)
from .services import is_device_online


def _create_device(request):
    serializer = DeviceCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serial = serializer.validated_data["serial"]
    if Device.objects.filter(serial=serial).exists():
        raise Conflict("Device serial already registered")
    try:
        with transaction.atomic():
            device = Device.objects.create(serial=serial, owner=request.user)
    except IntegrityError:
        raise Conflict("Device serial already registered")
    return Response(DeviceSerializer(device).data, status=status.HTTP_201_CREATED)


def _my_devices(owner):
    rows = []
    for device in Device.objects.filter(owner=owner).select_related("vehicle").order_by("id"):
        vehicle = getattr(device, "vehicle", None)
        rows.append(
            {
                "id": device.id,
                "serial": device.serial,
                "created_at": device.created_at,
                "vehicle_id": vehicle.id if vehicle else None,
                "vin": vehicle.vin if vehicle else None,
            }
        )
    return MyDeviceSerializer(rows, many=True).data


def _own_device_or_403(request, serial):
    device = request.user.device
    if device.serial != serial:
        raise PermissionDenied("Token does not belong to this device")
    return device


def _viewable_device(request, serial):
    """404 if the device does not exist; 403 if the caller does not own it."""
    device = Device.objects.filter(serial=serial).first()
    if device is None:
        raise NotFound("Device not found")
    if device.owner_id != request.user.id:
        raise PermissionDenied("Not enough permissions")
    return device


# ---------------------------------------------------------------- owners (user / company)
class DeviceCreateView(APIView):
    permission_classes = [IsUser]

    @extend_schema(request=DeviceCreateSerializer, responses={201: DeviceSerializer})
    def post(self, request):
        return _create_device(request)


class MyDevicesView(APIView):
    permission_classes = [IsUser]

    @extend_schema(responses=MyDeviceSerializer(many=True))
    def get(self, request):
        return Response(_my_devices(request.user))


class CompanyDeviceListCreateView(APIView):
    permission_classes = [IsCompany]

    @extend_schema(request=DeviceCreateSerializer, responses={201: DeviceSerializer})
    def post(self, request):
        return _create_device(request)

    @extend_schema(responses=MyDeviceSerializer(many=True))
    def get(self, request):
        return Response(_my_devices(request.user))


class HealthView(APIView):
    permission_classes = [IsAccount]

    @extend_schema(responses=HealthSerializer)
    def get(self, request, serial):
        device = _viewable_device(request, serial)
        return Response(
            {
                "serial": device.serial,
                "online": is_device_online(device),
                "last_heartbeat_at": device.last_heartbeat_at,
            }
        )


class RevokeDeviceTokenView(APIView):
    permission_classes = [IsAccount]

    @extend_schema(request=None, responses={204: None})
    def post(self, request, device_id):
        device = Device.objects.filter(pk=device_id).first()
        if device is None:
            raise NotFound("Device not found")
        if device.owner_id != request.user.id:
            raise PermissionDenied("Only the owner can revoke this device token")
        Device.objects.filter(pk=device.pk).update(token_version=F("token_version") + 1)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CommandCreateView(APIView):
    """Companies send commands to their own devices (staff do it from the admin panel)."""

    permission_classes = [IsCompany]

    @extend_schema(request=CommandCreateSerializer, responses={201: CommandSerializer})
    def post(self, request, serial):
        serializer = CommandCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        command_type = serializer.validated_data["command_type"]
        device = Device.objects.filter(serial=serial).first()
        if device is None:
            raise NotFound("Device not found")
        if device.owner_id != request.user.id:
            raise PermissionDenied("Device does not belong to your company")
        try:
            with transaction.atomic():
                device = Device.objects.select_for_update().get(pk=device.pk)
                if DeviceCommand.objects.filter(
                    device=device,
                    command_type=command_type,
                    status__in=[DeviceCommand.Status.PENDING, DeviceCommand.Status.DELIVERED],
                ).exists():
                    raise Conflict("An identical command is already pending or in progress")
                command = DeviceCommand.objects.create(
                    device=device, command_type=command_type, issued_by=request.user
                )
        except IntegrityError:
            raise Conflict("An identical command is already pending or in progress")
        return Response(CommandSerializer(command).data, status=status.HTTP_201_CREATED)


class CommandDetailView(APIView):
    permission_classes = [IsAccount]

    @extend_schema(responses=CommandSerializer)
    def get(self, request, serial, command_id):
        device = _viewable_device(request, serial)
        command = DeviceCommand.objects.filter(pk=command_id, device=device).first()
        if command is None:
            raise NotFound("Command not found")
        return Response(CommandSerializer(command).data)


# ---------------------------------------------------------------- device side
class HeartbeatView(APIView):
    permission_classes = [IsDevice]

    @extend_schema(request=None, responses={204: None})
    def post(self, request, serial):
        device = _own_device_or_403(request, serial)
        Device.objects.filter(pk=device.pk).update(last_heartbeat_at=timezone.now())
        return Response(status=status.HTTP_204_NO_CONTENT)


class PendingCommandsView(APIView):
    permission_classes = [IsDevice]

    @extend_schema(responses=CommandSerializer(many=True))
    def get(self, request, serial):
        device = _own_device_or_403(request, serial)
        with transaction.atomic():
            commands = list(
                DeviceCommand.objects.select_for_update()
                .filter(device=device, status=DeviceCommand.Status.PENDING)
                .order_by("id")
            )
            delivered_at = timezone.now()
            for command in commands:
                command.status = DeviceCommand.Status.DELIVERED
                command.delivered_at = delivered_at
                command.save(update_fields=["status", "delivered_at"])
        return Response(CommandSerializer(commands, many=True).data)


class CommandAckView(APIView):
    permission_classes = [IsDevice]

    @extend_schema(request=None, responses=CommandSerializer)
    def post(self, request, serial, command_id):
        device = _own_device_or_403(request, serial)
        with transaction.atomic():
            command = DeviceCommand.objects.select_for_update().filter(pk=command_id, device=device).first()
            if command is None:
                raise NotFound("Command not found")
            if command.status != DeviceCommand.Status.DELIVERED:
                raise Conflict("Command is not in delivered state")
            command.status = DeviceCommand.Status.ACKNOWLEDGED
            command.acknowledged_at = timezone.now()
            command.save(update_fields=["status", "acknowledged_at"])
        return Response(CommandSerializer(command).data)
