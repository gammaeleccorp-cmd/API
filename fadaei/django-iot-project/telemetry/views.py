from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from telemetry.models import TelemetryRecord
from telemetry.serializers import TelemetryRecordSerializer


class TelemetryListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        telemetry_records = TelemetryRecord.objects.filter(
            device__vehicle__owner=request.user
        )

        serializer = TelemetryRecordSerializer(
            telemetry_records,
            many=True
        )

        return Response(serializer.data)