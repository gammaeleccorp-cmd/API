from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.exceptions import Conflict
from accounts.permissions import IsCompany, IsDevice, IsUser
from vehicles.models import Vehicle

from .models import Telemetry
from .serializers import TelemetryCreateSerializer, TelemetrySerializer

LIMIT_PARAM = OpenApiParameter("limit", int, description="Max rows (1-1000, default 100)")


def _history(vehicle, request):
    """Newest first; only points recorded since the vehicle was (last) activated."""
    queryset = Telemetry.objects.filter(vehicle=vehicle).order_by("-recorded_at")
    if vehicle.activated_at is None:
        queryset = queryset.none()
    else:
        queryset = queryset.filter(recorded_at__gte=vehicle.activated_at)
    try:
        limit = min(max(int(request.query_params.get("limit", 100)), 1), 1000)
    except ValueError:
        limit = 100
    return Response(TelemetrySerializer(queryset[:limit], many=True).data)


class TelemetryCreateView(APIView):
    permission_classes = [IsDevice]

    @extend_schema(request=TelemetryCreateSerializer, responses={201: TelemetrySerializer})
    def post(self, request):
        serializer = TelemetryCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        device = request.user.device
        vehicle = Vehicle.objects.filter(device=device, is_active=True).first()
        if vehicle is None:
            raise Conflict("Device is not active on any vehicle")
        record = Telemetry.objects.create(
            device=device,
            vehicle=vehicle,
            latitude=data["latitude"],
            longitude=data["longitude"],
            speed=data.get("speed"),
            rpm=data.get("rpm"),
            fuel_level=data.get("fuel_level"),
            recorded_at=data.get("recorded_at") or timezone.now(),
        )
        return Response(TelemetrySerializer(record).data, status=status.HTTP_201_CREATED)


class UserVehicleTelemetryView(APIView):
    permission_classes = [IsUser]

    @extend_schema(parameters=[LIMIT_PARAM], responses=TelemetrySerializer(many=True))
    def get(self, request, vehicle_id):
        vehicle = Vehicle.objects.filter(pk=vehicle_id, owner=request.user).first()
        if vehicle is None:
            raise NotFound("Vehicle not found")
        return _history(vehicle, request)


class CompanyVehicleTelemetryView(APIView):
    permission_classes = [IsCompany]

    @extend_schema(parameters=[LIMIT_PARAM], responses=TelemetrySerializer(many=True))
    def get(self, request, vehicle_id):
        vehicle = Vehicle.objects.filter(pk=vehicle_id, owner=request.user).first()
        if vehicle is None:
            raise NotFound("Vehicle not found")
        return _history(vehicle, request)
