
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient

from vehicles.models import Vehicle


class VehicleAPITests(APITestCase):

    def setUp(self):
        User = get_user_model()

        self.user = User.objects.create_user(
            username="vehicle_owner",
            password="TestPassword123!"
        )

        self.other_user = User.objects.create_user(
            username="other_owner",
            password="TestPassword123!"
        )

        self.vehicle = Vehicle.objects.create(
            owner=self.user,
            name="Test Vehicle",
            brand="Toyota",
            model="Corolla",
            vin="TESTVIN0000000004"
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_user_can_view_own_vehicles(self):
        response = self.client.get("/api/vehicles/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]["vin"],
            self.vehicle.vin
        )

    def test_user_cannot_view_another_users_vehicle(self):
        self.client.force_authenticate(user=self.other_user)

        response = self.client.get(
            f"/api/vehicles/{self.vehicle.id}/"
        )

        self.assertEqual(response.status_code, 403)

    def test_owner_can_view_vehicle_detail(self):
        response = self.client.get(
            f"/api/vehicles/{self.vehicle.id}/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["vin"],
            self.vehicle.vin
        )

    def test_unauthenticated_user_cannot_view_vehicles(self):
        self.client.force_authenticate(user=None)

        response = self.client.get("/api/vehicles/")

        self.assertEqual(response.status_code, 401)
