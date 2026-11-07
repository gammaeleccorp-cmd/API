from rest_framework import serializers

from .models import Telemetry


class TelemetryCreateSerializer(serializers.Serializer):
    latitude = serializers.FloatField(min_value=-90, max_value=90)
    longitude = serializers.FloatField(min_value=-180, max_value=180)
    speed = serializers.FloatField(min_value=0, required=False, allow_null=True)
    rpm = serializers.FloatField(min_value=0, required=False, allow_null=True)
    fuel_level = serializers.FloatField(min_value=0, max_value=100, required=False, allow_null=True)
    recorded_at = serializers.DateTimeField(required=False, allow_null=True)


class TelemetrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Telemetry
        fields = [
            "id", "device", "vehicle", "latitude", "longitude",
            "speed", "rpm", "fuel_level", "recorded_at", "created_at",
        ]
        read_only_fields = fields
