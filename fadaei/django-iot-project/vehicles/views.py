from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from vehicles.models import Vehicle
from devices.permissions import IsVehicleOwner


class VehicleListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        vehicles = Vehicle.objects.filter(owner=request.user)

        return Response([
            {
                "id": vehicle.id,
                "name": vehicle.name,
                "brand": vehicle.brand,
                "model": vehicle.model,
                "vin": vehicle.vin,
            }
            for vehicle in vehicles
        ])


class VehicleDetailView(APIView):
    permission_classes = [IsAuthenticated, IsVehicleOwner]

    def get(self, request, pk):
        try:
            vehicle = Vehicle.objects.get(pk=pk)
        except Vehicle.DoesNotExist:
            return Response(
                {"error": "Vehicle not found."},
                status=404
            )

        self.check_object_permissions(request, vehicle)

        return Response({
            "id": vehicle.id,
            "name": vehicle.name,
            "brand": vehicle.brand,
            "model": vehicle.model,
            "vin": vehicle.vin,
        })
