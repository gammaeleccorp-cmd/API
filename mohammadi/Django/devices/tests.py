from rest_framework.test import APITestCase

from accounts.factories import (
    USER_A, USER_B, VIN1, activate_company_flow, activate_user_flow, bearer, headers_for, make_user,
)


class DeviceTests(APITestCase):
    def test_create_device_and_list_mine(self):
        make_user(USER_A)
        headers = headers_for(self.client, USER_A["mobile"])
        response = self.client.post("/api/devices/", {"serial": "DEV-001"}, format="json", **headers)
        self.assertEqual(response.status_code, 201)
        self.assertNotIn("device_token", response.json())
        mine = self.client.get("/api/devices/my/", **headers).json()
        self.assertEqual(len(mine), 1)
        self.assertIsNone(mine[0]["vehicle_id"])

    def test_duplicate_serial_and_missing_auth(self):
        make_user(USER_A)
        headers = headers_for(self.client, USER_A["mobile"])
        self.client.post("/api/devices/", {"serial": "DEV-001"}, format="json", **headers)
        self.assertEqual(self.client.post("/api/devices/", {"serial": "DEV-001"}, format="json", **headers).status_code, 409)
        self.assertEqual(self.client.post("/api/devices/", {"serial": "X"}, format="json").status_code, 401)


class HeartbeatAndHealthTests(APITestCase):
    def test_heartbeat_makes_device_online_for_its_owner_only(self):
        headers, device_headers, _ = activate_user_flow(self.client)
        self.assertEqual(self.client.post("/api/devices/DEV-001/heartbeat/", **device_headers).status_code, 204)
        self.assertEqual(self.client.post("/api/devices/OTHER/heartbeat/", **device_headers).status_code, 403)
        self.assertTrue(self.client.get("/api/devices/DEV-001/health/", **headers).json()["online"])
        make_user(USER_B)
        other = headers_for(self.client, USER_B["mobile"])
        self.assertEqual(self.client.get("/api/devices/DEV-001/health/", **other).status_code, 403)

    def test_health_is_offline_without_heartbeat(self):
        headers, _, _ = activate_user_flow(self.client)
        body = self.client.get("/api/devices/DEV-001/health/", **headers).json()
        self.assertFalse(body["online"])
        self.assertIsNone(body["last_heartbeat_at"])
        self.assertEqual(self.client.get("/api/devices/NOPE/health/", **headers).status_code, 404)


class DeviceTokenTests(APITestCase):
    def _device_id(self, headers):
        return self.client.get("/api/devices/my/", **headers).json()[0]["id"]

    def test_revoke_invalidates_old_token(self):
        headers, device_headers, _ = activate_user_flow(self.client)
        self.assertEqual(self.client.post("/api/devices/DEV-001/heartbeat/", **device_headers).status_code, 204)
        revoke = self.client.post(f"/api/devices/{self._device_id(headers)}/revoke-token/", **headers)
        self.assertEqual(revoke.status_code, 204)
        self.assertEqual(self.client.post("/api/devices/DEV-001/heartbeat/", **device_headers).status_code, 403)
        telemetry = self.client.post("/api/telemetry/", {"latitude": 1, "longitude": 1}, format="json", **device_headers)
        self.assertEqual(telemetry.status_code, 403)

    def test_only_owner_can_revoke(self):
        headers, _, _ = activate_user_flow(self.client)
        make_user(USER_B)
        other = headers_for(self.client, USER_B["mobile"])
        device_id = self._device_id(headers)
        self.assertEqual(self.client.post(f"/api/devices/{device_id}/revoke-token/", **other).status_code, 403)
        self.assertEqual(self.client.post("/api/devices/99999/revoke-token/", **headers).status_code, 404)

    def test_new_activation_after_revoke_issues_working_token(self):
        headers, old_device_headers, _ = activate_user_flow(self.client)
        self.client.post(f"/api/devices/{self._device_id(headers)}/revoke-token/", **headers)
        self.client.post(f"/api/vehicles/{VIN1}/deactivate/", **headers)
        response = self.client.post(
            "/api/vehicles/activate/",
            {"vin": VIN1, "national_id": USER_A["national_id"], "device_serial": "DEV-001"},
            format="json",
            **headers,
        )
        self.assertEqual(response.status_code, 200)
        new_headers = bearer(response.json()["device_token"])
        self.assertEqual(self.client.post("/api/devices/DEV-001/heartbeat/", **new_headers).status_code, 204)
        self.assertEqual(self.client.post("/api/devices/DEV-001/heartbeat/", **old_device_headers).status_code, 403)


class CommandTests(APITestCase):
    def test_command_lifecycle(self):
        headers, device_headers, _ = activate_company_flow(self.client, serial="DEV-C-001")
        created = self.client.post("/api/devices/DEV-C-001/commands/", {"command_type": "locate"}, format="json", **headers)
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.json()["status"], "pending")
        command_id = created.json()["id"]

        pending = self.client.get("/api/devices/DEV-C-001/commands/pending/", **device_headers).json()
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["status"], "delivered")
        self.assertEqual(self.client.get("/api/devices/DEV-C-001/commands/pending/", **device_headers).json(), [])

        ack = self.client.post(f"/api/devices/DEV-C-001/commands/{command_id}/ack/", **device_headers)
        self.assertEqual(ack.status_code, 200)
        self.assertEqual(ack.json()["status"], "acknowledged")
        again = self.client.post(f"/api/devices/DEV-C-001/commands/{command_id}/ack/", **device_headers)
        self.assertEqual(again.status_code, 409)
        detail = self.client.get(f"/api/devices/DEV-C-001/commands/{command_id}/", **headers)
        self.assertEqual(detail.json()["status"], "acknowledged")

    def test_duplicate_and_invalid_commands(self):
        headers, _, _ = activate_company_flow(self.client, serial="DEV-C-001")
        url = "/api/devices/DEV-C-001/commands/"
        self.assertEqual(self.client.post(url, {"command_type": "ignite"}, format="json", **headers).status_code, 201)
        self.assertEqual(self.client.post(url, {"command_type": "ignite"}, format="json", **headers).status_code, 409)
        self.assertEqual(self.client.post(url, {"command_type": "boom"}, format="json", **headers).status_code, 422)

    def test_regular_user_cannot_send_commands(self):
        headers, _, _ = activate_user_flow(self.client)
        response = self.client.post("/api/devices/DEV-001/commands/", {"command_type": "locate"}, format="json", **headers)
        self.assertEqual(response.status_code, 403)
