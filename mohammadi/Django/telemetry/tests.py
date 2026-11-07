from rest_framework.test import APITestCase

from accounts.factories import activate_company_flow, activate_user_flow


class TelemetryTests(APITestCase):
    def test_device_posts_and_owner_reads_history(self):
        headers, device_headers, body = activate_user_flow(self.client)
        response = self.client.post(
            "/api/telemetry/", {"latitude": 35.7, "longitude": 51.4, "speed": 60}, format="json", **device_headers
        )
        self.assertEqual(response.status_code, 201)
        history = self.client.get(f"/api/telemetry/vehicle/{body['id']}/", **headers)
        self.assertEqual(history.status_code, 200)
        self.assertEqual(len(history.json()), 1)

    def test_history_ignores_points_recorded_before_activation(self):
        headers, device_headers, body = activate_user_flow(self.client)
        old = {"latitude": 1, "longitude": 1, "recorded_at": "2020-01-01T00:00:00Z"}
        self.assertEqual(self.client.post("/api/telemetry/", old, format="json", **device_headers).status_code, 201)
        history = self.client.get(f"/api/telemetry/vehicle/{body['id']}/", **headers)
        self.assertEqual(history.json(), [])

    def test_only_device_tokens_can_post(self):
        headers, _, _ = activate_user_flow(self.client)
        point = {"latitude": 35.7, "longitude": 51.4}
        self.assertEqual(self.client.post("/api/telemetry/", point, format="json", **headers).status_code, 403)
        self.assertEqual(self.client.post("/api/telemetry/", point, format="json").status_code, 401)

    def test_invalid_coordinates_are_rejected(self):
        _, device_headers, _ = activate_user_flow(self.client)
        bad = {"latitude": 123, "longitude": 51.4}
        self.assertEqual(self.client.post("/api/telemetry/", bad, format="json", **device_headers).status_code, 422)

    def test_company_reads_its_vehicle_history(self):
        headers, device_headers, body = activate_company_flow(self.client)
        self.client.post("/api/telemetry/", {"latitude": 35.7, "longitude": 51.4}, format="json", **device_headers)
        history = self.client.get(f"/api/company/vehicles/{body['id']}/telemetry/", **headers)
        self.assertEqual(history.status_code, 200)
        self.assertEqual(len(history.json()), 1)
