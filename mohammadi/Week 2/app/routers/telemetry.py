from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db

from ..models import (
    Device,
    Telemetry,
    User,
    Vehicle,
)

from ..schemas import (
    TelemetryCreate,
    TelemetryResponse,
)


router = APIRouter(
    prefix="/telemetry",
    tags=["Telemetry"],
)


@router.post(
    "",
    response_model=TelemetryResponse,
    status_code=201,
)
def create_telemetry(
    data: TelemetryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    device = (
        db.query(Device)
        .filter(
            Device.serial
            == data.device_serial
        )
        .first()
    )

    if device is None:

        raise HTTPException(
            status_code=404,
            detail="Device not found",
        )

    vehicle = (
        db.query(Vehicle)
        .filter(
            Vehicle.device_id
            == device.id
        )
        .first()
    )

    if vehicle is None:

        raise HTTPException(
            status_code=404,
            detail=(
                "Device is not activated"
            ),
        )

    if vehicle.user_id != current_user.id:

        raise HTTPException(
            status_code=403,
            detail=(
                "You do not own this device"
            ),
        )

    telemetry = Telemetry(
        device_id=device.id,
        vehicle_id=vehicle.id,

        latitude=data.latitude,
        longitude=data.longitude,

        speed=data.speed,
        rpm=data.rpm,

        fuel_level=data.fuel_level,

        recorded_at=data.recorded_at,
    )

    db.add(telemetry)
    db.commit()
    db.refresh(telemetry)

    return telemetry


@router.get(
    "/vehicle/{vehicle_id}",
    response_model=list[TelemetryResponse],
)
def get_vehicle_telemetry(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    vehicle = (
        db.query(Vehicle)
        .filter(
            Vehicle.id == vehicle_id,
            Vehicle.user_id
            == current_user.id,
        )
        .first()
    )

    if vehicle is None:

        raise HTTPException(
            status_code=404,
            detail="Vehicle not found",
        )

    telemetry = (
        db.query(Telemetry)
        .filter(
            Telemetry.vehicle_id
            == vehicle.id
        )
        .order_by(
            Telemetry.recorded_at.desc()
        )
        .all()
    )

    return telemetry