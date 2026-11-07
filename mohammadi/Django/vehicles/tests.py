from rest_framework.test import APITestCase

from accounts.factories import (
    USER_A, USER_B, VIN1, VIN2, activate_company_flow, activate_user_flow, headers_for, make_company, make_user,
)


class UserVehicleTests(APITestCase):
    def test_create_vehicle_and_duplicate_vin(self):
        make_user(USER_A)
        headers = headers_for(self.client, USER_A["mobile"])
        response = self.client.post("/api/vehicles/", {"vin": VIN1}, format="json", **headers)
        self.assertEqual(response.status_code, 201)
        self.assertFalse(response.json()["is_active"])
        self.assertEqual(self.client.post("/api/vehicles/", {"vin": VIN1}, format="json", **headers).status_code, 409)
        self.assertEqual(self.client.post("/api/vehicles/", {"vin": VIN1}, format="json").status_code, 401)

    def test_activation_binds_device_and_returns_token(self):
        _, _, body = activate_user_flow(self.client)
        self.assertTrue(body["is_active"])
        self.assertTrue(body["device_token"])
        self.assertIsNotNone(body["device"])

    def test_activation_requires_matching_national_id(self):
        make_user(USER_A)
        headers = headers_for(self.client, USER_A["mobile"])
        self.client.post("/api/devices/", {"serial": "DEV-001"}, format="json", **headers)
        self.client.post("/api/vehicles/", {"vin": VIN1}, format="json", **headers)
        response = self.client.post(
            "/api/vehicles/activate/",
            {"vin": VIN1, "national_id": "0000000000", "device_serial": "DEV-001"},
            format="json",
            **headers,
        )
        self.assertEqual(response.status_code, 403)

    def test_device_cannot_be_active_on_two_vehicles(self):
        headers, _, _ = activate_user_flow(self.client)
        self.client.post("/api/vehicles/", {"vin": VIN2}, format="json", **headers)
        response = self.client.post(
            "/api/vehicles/activate/",
            {"vin": VIN2, "national_id": USER_A["national_id"], "device_serial": "DEV-001"},
            format="json",
            **headers,
        )
        self.assertEqual(response.status_code, 409)

    def test_vehicle_of_someone_else_cannot_be_activated(self):
        activate_user_flow(self.client, USER_A, serial="DEV-A", vin=VIN1)
        make_user(USER_B)
        other = headers_for(self.client, USER_B["mobile"])
        self.client.post("/api/devices/", {"serial": "DEV-B"}, format="json", **other)
        response = self.client.post(
            "/api/vehicles/activate/",
            {"vin": VIN1, "national_id": USER_B["national_id"], "device_serial": "DEV-B"},
            format="json",
            **other,
        )
        self.assertEqual(response.status_code, 403)

    def test_deactivate_then_activate_again(self):
        headers, _, _ = activate_user_flow(self.client)
        self.assertEqual(self.client.post(f"/api/vehicles/{VIN1}/deactivate/", **headers).status_code, 200)
        response = self.client.post(
            "/api/vehicles/activate/",
            {"vin": VIN1, "national_id": USER_A["national_id"], "device_serial": "DEV-001"},
            format="json",
            **headers,
        )
        self.assertEqual(response.status_code, 200)

    def test_vehicle_lists_are_private(self):
        headers, _, body = activate_user_flow(self.client)
        make_user(USER_B)
        other = headers_for(self.client, USER_B["mobile"])
        self.assertEqual(len(self.client.get("/api/vehicles/my/", **headers).json()), 1)
        self.assertEqual(self.client.get("/api/vehicles/my/", **other).json(), [])
        self.assertEqual(self.client.get(f"/api/vehicles/{body['id']}/", **other).status_code, 404)


class CompanyVehicleTests(APITestCase):
    def test_company_vehicle_is_owned_by_company(self):
        headers, _, body = activate_company_flow(self.client)
        me = self.client.get("/api/auth/me/", **headers).json()
        self.assertEqual(body["owner"], me["id"])

    def test_company_lists_are_isolated(self):
        ha, _, body = activate_company_flow(self.client, "company_a", "DEV-A", VIN1)
        activate_company_flow(self.client, "company_b", "DEV-B", VIN2)
        self.assertEqual(len(self.client.get("/api/company/vehicles/", **ha).json()), 1)
        hb = headers_for(self.client, "company_b")
        self.assertEqual(self.client.get(f"/api/company/vehicles/{body['id']}/", **hb).status_code, 404)

    def test_other_company_cannot_activate_vehicle(self):
        activate_company_flow(self.client, "company_a", "DEV-A", VIN1)
        # company_b registers its own device, then tries to take company_a's vehicle
        make_company("company_b", "Company B")
        hb = headers_for(self.client, "company_b")
        self.client.post("/api/company/devices/", {"serial": "DEV-B"}, format="json", **hb)
        response = self.client.post(
            "/api/company/vehicles/activate/", {"vin": VIN1, "device_serial": "DEV-B"}, format="json", **hb
        )
        self.assertEqual(response.status_code, 403)

    def test_user_cannot_use_company_endpoints(self):
        make_user(USER_A)
        headers = headers_for(self.client, USER_A["mobile"])
        self.assertEqual(self.client.get("/api/company/vehicles/", **headers).status_code, 403)
