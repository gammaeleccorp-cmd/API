"""
    python simulate_device.py
"""

import time
import random
import string
import requests

BASE_URL = "http://127.0.0.1:8000"
POLL_INTERVAL_SECONDS = 10


def random_mobile() -> str:
    return "09" + "".join(random.choices(string.digits, k=9))


def random_national_id() -> str:
    return "".join(random.choices(string.digits, k=10))


def random_vin() -> str:
    return "SIM" + "".join(random.choices(string.ascii_uppercase + string.digits, k=14))


def random_serial() -> str:
    return "SIM-DEV-" + "".join(random.choices(string.digits, k=6))


def setup_and_get_device_token() -> tuple[str, str]:

    mobile = random_mobile()
    national_id = random_national_id()
    password = "serial1234"

    requests.post(
        f"{BASE_URL}/auth/register",
        json={"mobile": mobile, "national_id": national_id, "password": password},
    ).raise_for_status()

    login_resp = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": mobile, "password": password},
    )
    login_resp.raise_for_status()
    user_token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {user_token}"}

    serial = random_serial()
    requests.post(
        f"{BASE_URL}/devices", json={"serial": serial}, headers=headers
    ).raise_for_status()
    print(f"[setup] Device created: {serial}")

    vin = random_vin()
    requests.post(
        f"{BASE_URL}/vehicles", json={"vin": vin}, headers=headers
    ).raise_for_status()

    activate_resp = requests.post(
        f"{BASE_URL}/vehicles/activate",
        json={"vin": vin, "national_id": national_id, "device_serial": serial},
        headers=headers,
    )
    activate_resp.raise_for_status()
    device_token = activate_resp.json()["device_token"]
    print(f"[setup] Vehicle activated; device_token received.")

    return serial, device_token


def execute_command(command: dict) -> None:

    command_type = command["command_type"]

    if command_type == "ignite":
        print(f"    [execute] Igniting engine (command #{command['id']})")
    elif command_type == "switch_off":
        print(f"    [execute] Turning off engine (command #{command['id']})")
    elif command_type == "locate":
        print(f"    [execute] Sending current location (command #{command['id']})")
    else:
        print(f"    [execute] Unknown Command type: {command_type}")

    time.sleep(1)


def poll_and_handle_commands(serial: str, headers: dict) -> None:

    resp = requests.get(
        f"{BASE_URL}/devices/{serial}/commands/pending",
        headers=headers,
    )

    if resp.status_code != 200:
        print(f"[commands] ⚠️ Error getting pending: {resp.status_code} - {resp.text}")
        return

    commands = resp.json()

    if not commands:
        return

    print(f"[commands] {len(commands)} new command(s) received:")

    for command in commands:
        execute_command(command)

        ack_resp = requests.post(
            f"{BASE_URL}/devices/{serial}/commands/{command['id']}/ack",
            headers=headers,
        )

        if ack_resp.status_code == 200:
            print(f"    ✅ ack sent (command #{command['id']})")
        else:
            print(f"    ❌ Error in ack: {ack_resp.status_code} - {ack_resp.text}")


def send_heartbeat(serial: str, headers: dict) -> None:
    resp = requests.post(
        f"{BASE_URL}/devices/{serial}/heartbeat",
        headers=headers,
    )
    if resp.status_code == 204:
        print(f"[heartbeat] ✅ sent ({time.strftime('%H:%M:%S')})")
    else:
        print(f"[heartbeat] ⚠️ Unexpected response: {resp.status_code}")


def main_loop(serial: str, device_token: str) -> None:
    headers = {"Authorization": f"Bearer {device_token}"}

    print(f"[main] Starting device loop (heartbeat + command polling) every {POLL_INTERVAL_SECONDS} seconds")

    try:
        while True:
            send_heartbeat(serial, headers)
            poll_and_handle_commands(serial, headers)
            time.sleep(POLL_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("\n[main] Stopped by user.")


if __name__ == "__main__":
    serial, device_token = setup_and_get_device_token()
    main_loop(serial, device_token)