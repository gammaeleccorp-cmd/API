"""Shared helpers for the test suites (not collected as tests)."""
from django.contrib.auth import get_user_model

User = get_user_model()

PASSWORD = "Str0ng-Pass-123"
USER_A = {"mobile": "09121234567", "national_id": "0499370899"}
USER_B = {"mobile": "09129999999", "national_id": "0084575948"}
VIN1 = "WVWZZZ1JZXW000001"
VIN2 = "WVWZZZ1JZXW000002"


def make_user(data=USER_A, password=PASSWORD):
    return User.objects.create_user(
        username=data["mobile"], mobile=data["mobile"], national_id=data["national_id"], password=password
    )


def make_company(username="company_a", name="Company A", password=PASSWORD):
    return User.objects.create_user(
        username=username, password=password, role=User.Role.COMPANY, company_name=name
    )


def bearer(token):
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


def login(client, username, password=PASSWORD):
    return client.post("/api/auth/login/", {"username": username, "password": password}, format="json")


def headers_for(client, username, password=PASSWORD):
    response = login(client, username, password)
    assert response.status_code == 200, response.content
    return bearer(response.json()["access"])


def activate_user_flow(client, data=USER_A, serial="DEV-001", vin=VIN1):
    """Create user, device and vehicle, then activate -> (user_headers, device_headers, body)."""
    if not User.objects.filter(mobile=data["mobile"]).exists():
        make_user(data)
    headers = headers_for(client, data["mobile"])
    assert client.post("/api/devices/", {"serial": serial}, format="json", **headers).status_code == 201
    assert client.post("/api/vehicles/", {"vin": vin}, format="json", **headers).status_code == 201
    response = client.post(
        "/api/vehicles/activate/",
        {"vin": vin, "national_id": data["national_id"], "device_serial": serial},
        format="json",
        **headers,
    )
    assert response.status_code == 200, response.content
    body = response.json()
    return headers, bearer(body["device_token"]), body


def activate_company_flow(client, username="company_a", serial="DEV-C-001", vin=VIN1):
    """Create company, device and vehicle, then activate -> (company_headers, device_headers, body)."""
    if not User.objects.filter(username=username).exists():
        make_company(username=username)
    headers = headers_for(client, username)
    assert client.post("/api/company/devices/", {"serial": serial}, format="json", **headers).status_code == 201
    assert client.post("/api/company/vehicles/", {"vin": vin}, format="json", **headers).status_code == 201
    response = client.post(
        "/api/company/vehicles/activate/", {"vin": vin, "device_serial": serial}, format="json", **headers
    )
    assert response.status_code == 200, response.content
    body = response.json()
    return headers, bearer(body["device_token"]), body
