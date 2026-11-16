from rest_framework import serializers

from vehicles.models import Vehicle


class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = [
            "id",
            "name",
            "brand",
            "model",
            "vin",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
        ]