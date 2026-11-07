from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase

from devices.models import Device, DeviceCommand
from vehicles.models import Vehicle

from .factories import PASSWORD, USER_A, USER_B, bearer, login, make_company, make_user

User = get_user_model()


class AuthAPITests(APITestCase):
    def test_register_with_mobile_national_id_and_password_only(self):
        payload = {**USER_A, "password": PASSWORD}
        response = self.client.post("/api/auth/register/", payload, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertNotIn("password", response.json())
        user = User.objects.get(mobile=USER_A["mobile"])
        self.assertEqual(user.username, USER_A["mobile"])  # username is the mobile
        self.assertEqual(user.role, "user")
        self.assertTrue(user.check_password(PASSWORD))

    def test_register_duplicates_are_conflicts(self):
        make_user(USER_A)
        same_mobile = {"mobile": USER_A["mobile"], "national_id": USER_B["national_id"], "password": PASSWORD}
        same_nid = {"mobile": USER_B["mobile"], "national_id": USER_A["national_id"], "password": PASSWORD}
        self.assertEqual(self.client.post("/api/auth/register/", same_mobile, format="json").status_code, 409)
        self.assertEqual(self.client.post("/api/auth/register/", same_nid, format="json").status_code, 409)

    def test_register_validation_errors(self):
        base = {**USER_A, "password": PASSWORD}
        for override in (
            {"mobile": "12345"},
            {"national_id": "1234567890"},  # wrong checksum
            {"national_id": "1111111111"},
            {"password": "12345678"},  # rejected by the password validators
        ):
            response = self.client.post("/api/auth/register/", {**base, **override}, format="json")
            self.assertEqual(response.status_code, 422, override)

    def test_login_with_mobile_as_username(self):
        make_user(USER_A)
        response = login(self.client, USER_A["mobile"])
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["role"], "user")
        self.assertTrue(body["access"] and body["refresh"])

    def test_login_wrong_password(self):
        make_user(USER_A)
        self.assertEqual(login(self.client, USER_A["mobile"], "wrong-pass").status_code, 401)

    def test_company_login_has_company_role(self):
        make_company()
        self.assertEqual(login(self.client, "company_a").json()["role"], "company")

    def test_me_requires_auth(self):
        make_user(USER_A)
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 401)
        self.assertEqual(self.client.get("/api/auth/me/", **bearer("garbage")).status_code, 401)
        access = login(self.client, USER_A["mobile"]).json()["access"]
        response = self.client.get("/api/auth/me/", **bearer(access))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["mobile"], USER_A["mobile"])

    def test_refresh_rotates_and_blacklists_old_token(self):
        make_user(USER_A)
        old = login(self.client, USER_A["mobile"]).json()["refresh"]
        response = self.client.post("/api/auth/refresh/", {"refresh": old}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.json()["refresh"], old)
        reuse = self.client.post("/api/auth/refresh/", {"refresh": old}, format="json")
        self.assertEqual(reuse.status_code, 401)

    def test_logout_blacklists_refresh_token(self):
        make_user(USER_A)
        refresh = login(self.client, USER_A["mobile"]).json()["refresh"]
        self.assertEqual(self.client.post("/api/auth/logout/", {"refresh": refresh}, format="json").status_code, 204)
        self.assertEqual(self.client.post("/api/auth/refresh/", {"refresh": refresh}, format="json").status_code, 401)

    def test_staff_accounts_cannot_use_the_api(self):
        User.objects.create_superuser(username="root", password=PASSWORD)
        self.assertEqual(login(self.client, "root").status_code, 401)


class AdminPanelTests(APITestCase):
    """The admin panel replaces the old admin role: companies, commands, force-deactivate."""

    def setUp(self):
        self.staff = User.objects.create_superuser(username="root", password=PASSWORD)
        self.client.force_login(self.staff)

    def test_changelists_and_add_pages_load(self):
        for url in (
            "/admin/accounts/user/",
            "/admin/accounts/company/",
            "/admin/devices/device/",
            "/admin/devices/devicecommand/",
            "/admin/vehicles/vehicle/",
            "/admin/telemetry/telemetry/",
            "/admin/notes/note/",
            "/admin/accounts/user/add/",
            "/admin/accounts/company/add/",
            "/admin/devices/devicecommand/add/",
        ):
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_regular_user_cannot_open_admin(self):
        self.client.logout()
        self.client.force_login(make_user(USER_A))
        self.assertEqual(self.client.get("/admin/").status_code, 302)

    def test_staff_creates_company_and_it_can_log_in(self):
        response = self.client.post(
            "/admin/accounts/company/add/",
            {
                "username": "acme",
                "usable_password": "true",
                "password1": "Comp-Pass-123x",
                "password2": "Comp-Pass-123x",
                "company_name": "Acme",
                "_save": "Save",
            },
        )
        self.assertEqual(response.status_code, 302, getattr(response, "context", None) and response.context["errors"])
        company = User.objects.get(username="acme")
        self.assertEqual(company.role, "company")
        self.client.logout()
        self.assertEqual(login(self.client, "acme", "Comp-Pass-123x").json()["role"], "company")

    def test_staff_sends_command_from_admin(self):
        owner = make_company()
        device = Device.objects.create(serial="DEV-ADM", owner=owner)
        response = self.client.post(
            "/admin/devices/devicecommand/add/",
            {"device": device.pk, "command_type": "locate", "_save": "Save"},
        )
        self.assertEqual(response.status_code, 302)
        command = DeviceCommand.objects.get(device=device)
        self.assertEqual(command.issued_by, self.staff)
        self.assertEqual(command.status, "pending")

    def test_staff_force_deactivates_vehicle(self):
        owner = make_user(USER_A)
        device = Device.objects.create(serial="DEV-ADM", owner=owner)
        vehicle = Vehicle.objects.create(
            vin="WVWZZZ1JZXW000009", owner=owner, device=device, is_active=True, activated_at=timezone.now()
        )
        response = self.client.post(
            "/admin/vehicles/vehicle/", {"action": "force_deactivate", "_selected_action": [vehicle.pk]}
        )
        self.assertEqual(response.status_code, 302)
        vehicle.refresh_from_db()
        self.assertFalse(vehicle.is_active)
        self.assertIsNone(vehicle.owner)
        self.assertIsNone(vehicle.device)
