from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import get_current_device, get_current_user
from ..database import get_db
from ..models import Device, Telemetry, User, Vehicle
from ..schemas import TelemetryCreate, TelemetryResponse





router = APIRouter(prefix="/telemetry", tags=["Telemetry"])






@router.post(
    "",
    response_model=TelemetryResponse,
    status_code=201,
)
def create_telemetry(
    data: TelemetryCreate,
    db: Session = Depends(get_db),
    device: Device = Depends(get_current_device),
):

    vehicle = device.vehicle

    if vehicle is None or not vehicle.is_active:
        raise HTTPException(
            status_code=404,
            detail="Device is not activated",
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
    current_user: User = Depends(get_current_user),
):
    vehicle = (
        db.query(Vehicle)
        .filter(
            Vehicle.id == vehicle_id,
            Vehicle.user_id == current_user.id,
        )
        .first()
    )

    if vehicle is None:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    query = db.query(Telemetry).filter(Telemetry.vehicle_id == vehicle.id)

    if vehicle.activated_at is not None:
        query = query.filter(Telemetry.recorded_at >= vehicle.activated_at)

    return query.order_by(Telemetry.recorded_at.desc()).all()
