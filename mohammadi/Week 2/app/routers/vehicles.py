from datetime import datetime

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
    ActivateVehicleRequest,
    VehicleCreate,
    VehicleResponse,
)


router = APIRouter(
    prefix="/vehicles",
    tags=["Vehicles"],
)


@router.post(
    "",
    response_model=VehicleResponse,
    status_code=201,
)
def create_vehicle(
    data: VehicleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    existing = (
        db.query(Vehicle)
        .filter(
            Vehicle.vin == data.vin
        )
        .first()
    )

    if existing:

        raise HTTPException(
            status_code=409,
            detail=(
                "Vehicle with this VIN "
                "already exists"
            ),
        )

    vehicle = Vehicle(
        vin=data.vin
    )

    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)

    return vehicle


@router.post(
    "/activate",
    response_model=VehicleResponse,
)
def activate_vehicle(
    data: ActivateVehicleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    if (
        current_user.national_id
        != data.national_id
    ):

        raise HTTPException(
            status_code=403,
            detail=(
                "National ID does not "
                "belong to current user"
            ),
        )

    vehicle = (
        db.query(Vehicle)
        .filter(
            Vehicle.vin == data.vin
        )
        .first()
    )

    if vehicle is None:

        raise HTTPException(
            status_code=404,
            detail="Vehicle not found",
        )

    if vehicle.user_id is not None:

        raise HTTPException(
            status_code=409,
            detail="Vehicle is already activated",
        )

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

    active_vehicle = (
        db.query(Vehicle)
        .filter(
            Vehicle.device_id
            == device.id
        )
        .first()
    )

    if active_vehicle is not None:

        raise HTTPException(
            status_code=409,
            detail=(
                "Device is already active "
                "on another vehicle"
            ),
        )


    vehicle.user_id = current_user.id

    vehicle.device_id = device.id

    vehicle.activated_at = datetime.utcnow()

    db.commit()
    db.refresh(vehicle)

    return vehicle


@router.get(
    "/my",
    response_model=list[VehicleResponse],
)
def get_my_vehicles(
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

    return vehicles


@router.get(
    "/{vehicle_id}",
    response_model=VehicleResponse,
)
def get_my_vehicle(
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

    return vehicle