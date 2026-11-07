from django.db import IntegrityError, transaction
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.exceptions import Conflict
from accounts.permissions import IsCompany, IsUser
from devices.models import Device

from .models import Vehicle
from .serializers import (
    ActivateVehicleSerializer,
    CompanyActivateVehicleSerializer,
    VehicleActivationSerializer,
    VehicleCreateSerializer,
    VehicleSerializer,
)
from .services import activate_vehicle, deactivate_vehicle


def _create_vehicle(request):
    serializer = VehicleCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    vin = serializer.validated_data["vin"]
    if Vehicle.objects.filter(vin=vin).exists():
        raise Conflict("VIN already registered")
    try:
        with transaction.atomic():
            vehicle = Vehicle.objects.create(vin=vin, owner=request.user)
    except IntegrityError:
        raise Conflict("VIN already registered")
    return Response(VehicleSerializer(vehicle).data, status=status.HTTP_201_CREATED)


def _vehicle_for_activation(vin, owner):
    vehicle = Vehicle.objects.filter(vin=vin).first()
    if vehicle is None:
        raise NotFound("Vehicle not found")
    if vehicle.owner_id not in (None, owner.id):
        raise PermissionDenied("Vehicle belongs to someone else")
    return vehicle


def _device_for_activation(serial, owner):
    device = Device.objects.filter(serial=serial).first()
    if device is None:
        raise NotFound("Device not found")
    if device.owner_id != owner.id:
        raise PermissionDenied("Device does not belong to you")
    return device


def _owned_vehicle_or_404(owner, **lookup):
    vehicle = Vehicle.objects.filter(owner=owner, **lookup).first()
    if vehicle is None:
        raise NotFound("Vehicle not found")
    return vehicle


# ------------------------------------------------------------------ user
class VehicleCreateView(APIView):
    permission_classes = [IsUser]

    @extend_schema(request=VehicleCreateSerializer, responses={201: VehicleSerializer})
    def post(self, request):
        return _create_vehicle(request)


class MyVehiclesView(APIView):
    permission_classes = [IsUser]

    @extend_schema(responses=VehicleSerializer(many=True))
    def get(self, request):
        queryset = Vehicle.objects.filter(owner=request.user).order_by("id")
        return Response(VehicleSerializer(queryset, many=True).data)


class MyVehicleDetailView(APIView):
    permission_classes = [IsUser]

    @extend_schema(responses=VehicleSerializer)
    def get(self, request, vehicle_id):
        return Response(VehicleSerializer(_owned_vehicle_or_404(request.user, pk=vehicle_id)).data)


class VehicleActivateView(APIView):
    permission_classes = [IsUser]

    @extend_schema(request=ActivateVehicleSerializer, responses=VehicleActivationSerializer)
    def post(self, request):
        serializer = ActivateVehicleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = request.user
        if data["national_id"] != user.national_id:
            raise PermissionDenied("National ID does not match the logged-in user")
        vehicle = _vehicle_for_activation(data["vin"], user)
        device = _device_for_activation(data["device_serial"], user)
        vehicle = activate_vehicle(vehicle, device, user)
        return Response(VehicleActivationSerializer(vehicle).data)


class VehicleDeactivateView(APIView):
    permission_classes = [IsUser]

    @extend_schema(request=None, responses=VehicleSerializer)
    def post(self, request, vin):
        vehicle = _owned_vehicle_or_404(request.user, vin=vin)
        return Response(VehicleSerializer(deactivate_vehicle(vehicle)).data)


# ------------------------------------------------------------------ company
class CompanyVehicleListCreateView(APIView):
    permission_classes = [IsCompany]

    @extend_schema(request=VehicleCreateSerializer, responses={201: VehicleSerializer})
    def post(self, request):
        return _create_vehicle(request)

    @extend_schema(responses=VehicleSerializer(many=True))
    def get(self, request):
        queryset = Vehicle.objects.filter(owner=request.user).order_by("id")
        return Response(VehicleSerializer(queryset, many=True).data)


class CompanyVehicleDetailView(APIView):
    permission_classes = [IsCompany]

    @extend_schema(responses=VehicleSerializer)
    def get(self, request, vehicle_id):
        return Response(VehicleSerializer(_owned_vehicle_or_404(request.user, pk=vehicle_id)).data)


class CompanyVehicleActivateView(APIView):
    permission_classes = [IsCompany]

    @extend_schema(request=CompanyActivateVehicleSerializer, responses=VehicleActivationSerializer)
    def post(self, request):
        serializer = CompanyActivateVehicleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        company = request.user
        vehicle = _vehicle_for_activation(data["vin"], company)
        device = _device_for_activation(data["device_serial"], company)
        vehicle = activate_vehicle(vehicle, device, company)
        return Response(VehicleActivationSerializer(vehicle).data)


class CompanyVehicleDeactivateView(APIView):
    permission_classes = [IsCompany]

    @extend_schema(request=None, responses=VehicleSerializer)
    def post(self, request, vin):
        vehicle = _owned_vehicle_or_404(request.user, vin=vin)
        return Response(VehicleSerializer(deactivate_vehicle(vehicle)).data)
