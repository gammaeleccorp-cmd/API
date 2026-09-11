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
    MyDeviceResponse,
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
    current_user: User = Depends(get_current_user),
):

    existing = (
        db.query(Device)
        .filter(Device.serial == data.serial)
        .first()
    )

    if existing:
        raise HTTPException(status_code=409, detail="Device already exists")

    device = Device(
        serial=data.serial,
        owner_user_id=current_user.id,
    )

    db.add(device)
    db.commit()
    db.refresh(device)

    return device






@router.get(
    "/my",
    response_model=list[MyDeviceResponse],
)
def get_my_devices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    devices = (
        db.query(Device)
        .filter(Device.owner_user_id == current_user.id)
        .all()
    )

    result = []

    for device in devices:
        result.append(
            {
                "id": device.id,
                "serial": device.serial,
                "created_at": device.created_at,
                "vehicle_id": device.vehicle.id if device.vehicle else None,
                "vin": device.vehicle.vin if device.vehicle else None,
            }
        )

    return result