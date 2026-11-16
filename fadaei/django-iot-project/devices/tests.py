
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient

from devices.models import Device
from vehicles.models import Vehicle


class DeviceActivationAPITests(APITestCase):

    def setUp(self):
        User = get_user_model()

        self.user = User.objects.create_user(
            username="device_owner",
            password="TestPassword123!"
        )

        self.device = Device.objects.create(
            serial_number="TEST-DEVICE-001"
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.activation_url = "/api/devices/activate/"

        self.valid_data = {
            "serial_number": "TEST-DEVICE-001",
            "name": "My Test Car",
            "brand": "Toyota",
            "model": "Corolla",
            "vin": "TESTDEVICEVIN0001"
        }

    def test_user_can_activate_device(self):
        response = self.client.post(
            self.activation_url,
            self.valid_data,
            format="json"
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.data["message"],
            "Device activated successfully."
        )

        self.device.refresh_from_db()

        self.assertIsNotNone(self.device.vehicle)
        self.assertEqual(
            self.device.vehicle.owner,
            self.user
        )

        self.assertEqual(
            Vehicle.objects.count(),
            1
        )

    def test_user_cannot_activate_device_twice(self):
        first_response = self.client.post(
            self.activation_url,
            self.valid_data,
            format="json"
        )

        self.assertEqual(first_response.status_code, 201)

        second_data = self.valid_data.copy()
        second_data["vin"] = "TESTDEVICEVIN0002"

        second_response = self.client.post(
            self.activation_url,
            second_data,
            format="json"
        )

        self.assertEqual(second_response.status_code, 400)
        self.assertEqual(
            second_response.data["error"],
            "This device has already been activated."
        )

        self.assertEqual(Vehicle.objects.count(), 1)

    def test_activation_fails_for_unknown_device(self):
        data = self.valid_data.copy()
        data["serial_number"] = "UNKNOWN-DEVICE"

        response = self.client.post(
            self.activation_url,
            data,
            format="json"
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["error"],
            "Device not found."
        )

        self.assertEqual(Vehicle.objects.count(), 0)

    def test_unauthenticated_user_cannot_activate_device(self):
        self.client.force_authenticate(user=None)

        response = self.client.post(
            self.activation_url,
            self.valid_data,
            format="json"
        )

        self.assertEqual(response.status_code, 401)

        self.assertEqual(Vehicle.objects.count(), 0)

    def test_activation_fails_with_invalid_vin(self):
        data = self.valid_data.copy()
        data["vin"] = "INVALID-VIN-12345"

        response = self.client.post(
            self.activation_url,
            data,
            format="json"
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("vin", response.data)

        self.assertEqual(Vehicle.objects.count(), 0)
