from rest_framework import serializers

from telemetry.models import TelemetryRecord


class TelemetryRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelemetryRecord
        fields = [
            "id",
            "device",
            "data",
            "recorded_at",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
        ]