from rest_framework import serializers

from .models import Device, DeviceCommand


class DeviceCreateSerializer(serializers.Serializer):
    serial = serializers.CharField(min_length=1, max_length=100)


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ["id", "serial", "owner", "last_heartbeat_at", "created_at"]
        read_only_fields = fields


class MyDeviceSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    serial = serializers.CharField()
    created_at = serializers.DateTimeField()
    vehicle_id = serializers.IntegerField(allow_null=True)
    vin = serializers.CharField(allow_null=True)


class HealthSerializer(serializers.Serializer):
    serial = serializers.CharField()
    online = serializers.BooleanField()
    last_heartbeat_at = serializers.DateTimeField(allow_null=True)


class CommandCreateSerializer(serializers.Serializer):
    command_type = serializers.ChoiceField(choices=DeviceCommand.CommandType.choices)


class CommandSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceCommand
        fields = [
            "id", "device", "command_type", "status", "issued_by",
            "created_at", "delivered_at", "acknowledged_at",
        ]
        read_only_fields = fields
