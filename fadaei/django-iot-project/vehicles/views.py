from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from vehicles.models import Vehicle
from vehicles.serializers import VehicleSerializer
from devices.permissions import IsVehicleOwner


class VehicleListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        vehicles = Vehicle.objects.filter(owner=request.user)

        serializer = VehicleSerializer(
            vehicles,
            many=True
        )

        return Response(serializer.data)


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

        serializer = VehicleSerializer(vehicle)

        return Response(serializer.data)