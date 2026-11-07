"""Device simulator (no hardware needed): heartbeat, poll + ack commands, send telemetry.

    python scripts/simulate_device.py --serial DEV-001 --token <device_token> [--base http://127.0.0.1:8000]

The device token is returned once by the vehicle activation endpoint.
"""

import argparse
import json
import random
import time
import urllib.request


def call(base, token, method, path, body=None):
    request = urllib.request.Request(
        base + path,
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request) as response:
        raw = response.read()
        return json.loads(raw) if raw else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--serial", required=True)
    parser.add_argument("--token", required=True)
    parser.add_argument("--base", default="http://127.0.0.1:8000")
    parser.add_argument("--interval", type=float, default=5)
    args = parser.parse_args()

    lat, lon = 35.70, 51.40
    while True:
        call(args.base, args.token, "POST", f"/api/devices/{args.serial}/heartbeat/")
        for command in call(args.base, args.token, "GET", f"/api/devices/{args.serial}/commands/pending/"):
            print("executing", command["command_type"])
            call(args.base, args.token, "POST", f"/api/devices/{args.serial}/commands/{command['id']}/ack/")
        lat += random.uniform(-0.001, 0.001)
        lon += random.uniform(-0.001, 0.001)
        call(
            args.base,
            args.token,
            "POST",
            "/api/telemetry/",
            {
                "latitude": lat,
                "longitude": lon,
                "speed": random.uniform(0, 90),
                "rpm": random.uniform(800, 3500),
                "fuel_level": random.uniform(10, 90),
            },
        )
        print("tick", round(lat, 5), round(lon, 5))
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
