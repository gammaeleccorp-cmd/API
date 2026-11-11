
from rest_framework import serializers


class DeviceActivationSerializer(serializers.Serializer):
    serial_number = serializers.CharField(max_length=100)

    name = serializers.CharField(max_length=100)
    brand = serializers.CharField(max_length=100)
    model = serializers.CharField(max_length=100)
    vin = serializers.CharField(max_length=17, min_length=17)

    def validate_vin(self, value):
        if not value.isalnum():
            raise serializers.ValidationError(
                "VIN must contain only letters and numbers."
            )

        return value.upper()
