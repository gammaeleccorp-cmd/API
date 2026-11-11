
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from devices.serializers import DeviceActivationSerializer
from devices.services import activate_device


class DeviceActivationView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = DeviceActivationSerializer(data=request.data)

        if serializer.is_valid():

            try:
                vehicle = activate_device(
                    user=request.user,
                    **serializer.validated_data
                )

                return Response(
                    {
                        "message": "Device activated successfully.",
                        "vehicle_id": vehicle.id,
                        "vehicle_name": vehicle.name,
                        "device_serial": vehicle.device.serial_number
                    },
                    status=status.HTTP_201_CREATED
                )

            except ValueError as error:
                return Response(
                    {"error": str(error)},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
