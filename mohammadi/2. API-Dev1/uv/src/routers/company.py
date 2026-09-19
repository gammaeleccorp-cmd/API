
from datetime import datetime, timezone

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from ..auth import get_current_company, create_access_token
from ..database import get_db

from ..models import (
    Company,
    Device,
    Telemetry,
    Vehicle,
)

from ..schemas import (
    DeviceCreate,
    DeviceResponse,
    CompanyActivateVehicleRequest,
    CompanyResponse,
    CompanyDeviceResponse,
    TelemetryResponse,
    VehicleActivationResponse,
    VehicleCreate,
    VehicleResponse,
)







router = APIRouter(
    prefix="/company",
    tags=["Company"],
)






@router.get(
    "/me",
    response_model=CompanyResponse,
)
def get_company_me(
    current_company: Company = Depends(get_current_company),
):
    return current_company





@router.post(
    "/devices",
    response_model=DeviceResponse,
    status_code=201,
)
def create_company_device(
    data: DeviceCreate,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_company),
):

    existing = (
        db.query(Device)
        .filter(Device.serial == data.serial)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Device already exists",
        )

    device = Device(
        serial=data.serial,
        owner_company_id=current_company.id,
    )

    db.add(device)
    db.commit()
    db.refresh(device)


    return device





@router.get(
    "/devices",
    response_model=list[CompanyDeviceResponse],
)
def list_company_devices(
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_company),
):

    devices = (
        db.query(Device)
        .filter(Device.owner_company_id == current_company.id)
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





@router.post(
    "/vehicles",
    response_model=VehicleResponse,
    status_code=201,
)
def create_vehicle(
    data: VehicleCreate,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_company),
):

    existing = (
        db.query(Vehicle)
        .filter(Vehicle.vin == data.vin)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Vehicle with this VIN already exists",
        )

    vehicle = Vehicle(vin=data.vin)

    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)

    return vehicle





@router.post(
    "/vehicles/activate",
    response_model=VehicleActivationResponse,
)
def activate_company_vehicle(
    data: CompanyActivateVehicleRequest,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_company),
):

    vehicle = (
        db.query(Vehicle)
        .filter(Vehicle.vin == data.vin)
        .first()
    )

    if vehicle is None:
        raise HTTPException(
            status_code=404,
            detail="Vehicle not found",
        )

    if vehicle.is_active:
        raise HTTPException(
            status_code=409,
            detail="Vehicle is already activated",
        )

    device = (
        db.query(Device)
        .filter(Device.serial == data.device_serial)
        .first()
    )

    if device is None:
        raise HTTPException(
            status_code=404,
            detail="Device not found",
        )

    if device.owner_company_id != current_company.id:
        raise HTTPException(
            status_code=403,
            detail="Your company does not own this device",
        )
    
    conflicting_vehicle = (
        db.query(Vehicle)
        .filter(
            Vehicle.device_id == device.id,
            Vehicle.is_active == True,
        )
        .first()
    )

    if conflicting_vehicle is not None:
        raise HTTPException(
            status_code=409,
            detail="Device is already active on another vehicle",
        )

    vehicle.company_id = current_company.id
    vehicle.user_id = None
    vehicle.device_id = device.id
    vehicle.is_active = True
    vehicle.activated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(vehicle)

    device_token = create_access_token(
        subject_id=device.id,
        role="device",
        username=device.serial,
        no_expiry=True,
    )

    return {
        "id": vehicle.id,
        "vin": vehicle.vin,
        "user_id": vehicle.user_id,
        "company_id": vehicle.company_id,
        "device_id": vehicle.device_id,
        "is_active": vehicle.is_active,
        "activated_at": vehicle.activated_at,
        "device_token": device_token,
    }





@router.post(
    "/vehicles/{vin}/deactivate",
    response_model=VehicleResponse,
)
def deactivate_company_vehicle(
    vin: str,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_company),
):

    vehicle = (
        db.query(Vehicle)
        .filter(Vehicle.vin == vin)
        .first()
    )

    if vehicle is None:
        raise HTTPException(
            status_code=404,
            detail="Vehicle not found",
        )

    if vehicle.company_id != current_company.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to deactivate this vehicle",
        )

    if not vehicle.is_active:
        raise HTTPException(
            status_code=409,
            detail="Vehicle is not activated",
        )

    vehicle.company_id = None
    vehicle.device_id = None
    vehicle.is_active = False

    db.commit()
    db.refresh(vehicle)

    return vehicle





@router.get(
    "/vehicles",
    response_model=list[VehicleResponse],
)
def list_company_vehicles(
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_company),
):
    return (
        db.query(Vehicle)
        .filter(Vehicle.company_id == current_company.id)
        .all()
    )





@router.get(
    "/vehicles/{vehicle_id}",
    response_model=VehicleResponse,
)
def get_company_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_company),
):

    vehicle = (
        db.query(Vehicle)
        .filter(
            Vehicle.id == vehicle_id,
            Vehicle.company_id == current_company.id,
        )
        .first()
    )

    if vehicle is None:
        raise HTTPException(
            status_code=404,
            detail="Vehicle not found",
        )

    return vehicle





@router.get(
    "/vehicles/{vehicle_id}/telemetry",
    response_model=list[TelemetryResponse],
)
def get_company_vehicle_telemetry(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_company: Company = Depends(get_current_company),
):

    vehicle = (
        db.query(Vehicle)
        .filter(
            Vehicle.id == vehicle_id,
            Vehicle.company_id == current_company.id,
        )
        .first()
    )

    if vehicle is None:
        raise HTTPException(
            status_code=404,
            detail="Vehicle not found",
        )

    query = db.query(Telemetry).filter(
        Telemetry.vehicle_id == vehicle.id
    )

    if vehicle.activated_at is not None:
        query = query.filter(
            Telemetry.recorded_at >= vehicle.activated_at
        )

    return query.order_by(Telemetry.recorded_at.desc()).all()