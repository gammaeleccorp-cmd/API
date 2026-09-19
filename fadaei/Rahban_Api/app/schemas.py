from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator





class RegisterRequest(BaseModel):
    mobile: str = Field(
        min_length=11,
        max_length=11,
        pattern=r"^09\d{9}$",
        examples=["09121234567"],
    )
    national_id: str = Field(
        min_length=10,
        max_length=10,
        pattern=r"^\d{10}$",
        examples=["0012345678"],
    )
    password: str = Field(
        min_length=8,
        max_length=255,
        examples=["Ali@123456"],
    )





class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int | None
    role: str = Field(
        examples=["user", "company", "admin"],
    )






class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    mobile: str
    national_id: str
    created_at: datetime







class DeviceCreate(BaseModel):
    serial: str = Field(
        min_length=1,
        max_length=100,
        examples=["DEV-TRK-0001"],
    )





class DeviceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    serial: str
    created_at: datetime





class MyDeviceResponse(BaseModel):
    id: int
    serial: str
    created_at: datetime
    vehicle_id: int | None = None
    vin: str | None = None





class CompanyDeviceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    serial: str
    created_at: datetime
    vehicle_id: int | None = None
    vin: str | None = None





class DeviceHealthResponse(BaseModel):
    serial: str
    online: bool
    last_heartbeat_at: datetime | None





class DeviceCommandCreate(BaseModel):
    command: Literal["ignite", "switch_off", "locate"]





class DeviceCommandResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: int
    command: str
    status: Literal["pending", "delivered", "acknowledged"]
    created_at: datetime
    delivered_at: datetime | None
    acknowledged_at: datetime | None







class VehicleCreate(BaseModel):
    vin: str = Field(
        min_length=17,
        max_length=17,
        examples=["WVWZZZ1JZXW000001"],
    )





class ActivateVehicleRequest(BaseModel):
    vin: str = Field(
        min_length=17,
        max_length=17,
        examples=["WVWZZZ1JZXW000001"],
    )
    national_id: str = Field(
        min_length=10,
        max_length=10,
        pattern=r"^\d{10}$",
        examples=["0012345678"],
    )
    device_serial: str = Field(
        min_length=1,
        max_length=100,
        examples=["DEV-TRK-0001"],
    )





class CompanyActivateVehicleRequest(BaseModel):

    vin: str = Field(
        min_length=17,
        max_length=17,
        examples=["WVWZZZ1JZXW000001"],
    )
    device_serial: str = Field(
        min_length=1,
        max_length=100,
        examples=["DEV-TRK-0001"],
    )






class VehicleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    vin: str
    user_id: int | None
    company_id: int | None
    device_id: int | None
    is_active: bool
    activated_at: datetime | None




class VehicleActivationResponse(BaseModel):

    id: int
    vin: str
    user_id: int | None
    company_id: int | None
    device_id: int | None
    is_active: bool
    activated_at: datetime | None
    device_token: str





class TelemetryCreate(BaseModel):

    latitude: float | None = Field(default=None, examples=[35.6892])
    longitude: float | None = Field(default=None, examples=[51.3890])
    speed: float | None = Field(default=None, examples=[72.5])
    rpm: float | None = Field(default=None, examples=[2800])
    fuel_level: float | None = Field(default=None, examples=[63.0])

    recorded_at: datetime = Field(
        examples=["2026-09-05T10:30:00Z"],
    )

    @field_validator("recorded_at")
    @classmethod
    def normalize_recorded_at(cls, value: datetime) -> datetime:
        if value.tzinfo is not None:
            value = value.astimezone(timezone.utc).replace(tzinfo=None)
        return value





class TelemetryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: int
    vehicle_id: int
    latitude: float | None
    longitude: float | None
    speed: float | None
    rpm: float | None
    fuel_level: float | None
    recorded_at: datetime





class CompanyCreate(BaseModel):

    name: str = Field(
        min_length=1,
        max_length=255,
        examples=["دیجی کالا"],
    )
    username: str = Field(
        min_length=3,
        max_length=50,
        examples=["Digik@l@2026"],
    )
    password: str = Field(
        min_length=8,
        max_length=255,
        examples=["digi@1000"],
    )





class CompanyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    username: str
    created_at: datetime






class AdminUserListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    mobile: str
    national_id: str
    created_at: datetime





class RootResponse(BaseModel):
    message: str
    version: str
