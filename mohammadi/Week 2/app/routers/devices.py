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
    User,
    Vehicle,
)

from ..schemas import (
    DeviceCreate,
    DeviceResponse,
)


router = APIRouter(
    prefix="/devices",
    tags=["Devices"],
)


@router.post(
    "",
    response_model=DeviceResponse,
    status_code=201,
)
def create_device(
    data: DeviceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    existing = (
        db.query(Device)
        .filter(
            Device.serial == data.serial
        )
        .first()
    )

    if existing:

        raise HTTPException(
            status_code=409,
            detail="Device already exists",
        )

    device = Device(
        serial=data.serial
    )

    db.add(device)
    db.commit()
    db.refresh(device)

    return device


@router.get(
    "/my",
)
def get_my_devices(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    vehicles = (
        db.query(Vehicle)
        .filter(
            Vehicle.user_id
            == current_user.id
        )
        .all()
    )

    result = []

    for vehicle in vehicles:

        if vehicle.device:

            result.append(
                {
                    "id": vehicle.device.id,
                    "serial": vehicle.device.serial,
                    "vehicle_id": vehicle.id,
                    "vin": vehicle.vin,
                }
            )

    return result