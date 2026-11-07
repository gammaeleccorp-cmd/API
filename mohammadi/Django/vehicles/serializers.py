from rest_framework import serializers

from .models import Vehicle

VIN_RULES = dict(min_length=17, max_length=17)


class VehicleCreateSerializer(serializers.Serializer):
    vin = serializers.CharField(**VIN_RULES)


class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ["id", "vin", "owner", "device", "is_active", "activated_at", "created_at"]
        read_only_fields = fields


class VehicleActivationSerializer(VehicleSerializer):
    device_token = serializers.CharField(read_only=True)

    class Meta(VehicleSerializer.Meta):
        fields = VehicleSerializer.Meta.fields + ["device_token"]
        read_only_fields = fields


class ActivateVehicleSerializer(serializers.Serializer):
    vin = serializers.CharField(**VIN_RULES)
    national_id = serializers.RegexField(r"^[0-9]{10}$", max_length=10)
    device_serial = serializers.CharField(min_length=1, max_length=100)


class CompanyActivateVehicleSerializer(serializers.Serializer):
    vin = serializers.CharField(**VIN_RULES)
    device_serial = serializers.CharField(min_length=1, max_length=100)
