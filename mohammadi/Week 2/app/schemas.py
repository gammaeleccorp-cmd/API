from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RegisterRequest(BaseModel):
    mobile: str
    national_id: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


class UserResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    mobile: str
    national_id: str
    created_at: datetime


class DeviceCreate(BaseModel):
    serial: str


class DeviceResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    serial: str
    created_at: datetime


class VehicleCreate(BaseModel):
    vin: str


class ActivateVehicleRequest(BaseModel):
    vin: str
    national_id: str
    device_serial: str


class VehicleResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    vin: str
    user_id: int | None
    device_id: int | None
    activated_at: datetime | None



class TelemetryCreate(BaseModel):
    device_serial: str

    latitude: float | None = None
    longitude: float | None = None

    speed: float | None = None
    rpm: float | None = None

    fuel_level: float | None = None

    recorded_at: datetime


class TelemetryResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int

    device_id: int
    vehicle_id: int

    latitude: float | None
    longitude: float | None

    speed: float | None
    rpm: float | None

    fuel_level: float | None

    recorded_at: datetime