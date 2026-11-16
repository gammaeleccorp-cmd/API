
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient

from vehicles.models import Vehicle
from devices.models import Device
from telemetry.models import TelemetryRecord


class TelemetryAPITests(APITestCase):

    def setUp(self):
        User = get_user_model()

        self.user = User.objects.create_user(
            username="telemetry_owner",
            password="TestPassword123!"
        )

        self.other_user = User.objects.create_user(
            username="other_telemetry_owner",
            password="TestPassword123!"
        )

        self.vehicle = Vehicle.objects.create(
            owner=self.user,
            name="My Vehicle",
            brand="Toyota",
            model="Corolla",
            vin="TELEMETRYVIN0001"
        )

        self.other_vehicle = Vehicle.objects.create(
            owner=self.other_user,
            name="Other Vehicle",
            brand="Kia",
            model="Cerato",
            vin="TELEMETRYVIN0002"
        )

        self.device = Device.objects.create(
            vehicle=self.vehicle,
            serial_number="TELEMETRY-DEVICE-001"
        )

        self.other_device = Device.objects.create(
            vehicle=self.other_vehicle,
            serial_number="TELEMETRY-DEVICE-002"
        )

        self.own_record = TelemetryRecord.objects.create(
            device=self.device,
            data={"speed": 80, "temperature": 25},
            recorded_at=timezone.now()
        )

        self.other_record = TelemetryRecord.objects.create(
            device=self.other_device,
            data={"speed": 100, "temperature": 30},
            recorded_at=timezone.now()
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_user_can_view_own_telemetry(self):
        response = self.client.get("/api/telemetry/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]["id"],
            self.own_record.id
        )

    def test_user_cannot_view_other_users_telemetry(self):
        response = self.client.get("/api/telemetry/")

        returned_ids = [
            record["id"] for record in response.data
        ]

        self.assertNotIn(
            self.other_record.id,
            returned_ids
        )

    def test_unauthenticated_user_cannot_view_telemetry(self):
        self.client.force_authenticate(user=None)

        response = self.client.get("/api/telemetry/")

        self.assertEqual(response.status_code, 401)
