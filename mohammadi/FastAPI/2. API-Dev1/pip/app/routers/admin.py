from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from ..auth import get_current_admin, hash_password
from ..database import get_db

from ..models import (
    Admin,
    Company,
    Device,
    User,
    Vehicle,
)

from ..schemas import (
    AdminUserListItem,
    CompanyCreate,
    CompanyResponse,
    DeviceResponse,
    VehicleResponse,
)





router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)



@router.post(
    "/companies",
    response_model=CompanyResponse,
    status_code=201,
)
def create_company(
    data: CompanyCreate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):

    existing = (
        db.query(Company)
        .filter(Company.username == data.username)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Company username already exists",
        )

    company = Company(
        name=data.name,
        username=data.username,
        password_hash=hash_password(data.password),
    )

    db.add(company)
    db.commit()
    db.refresh(company)

    return company





@router.get(
    "/companies",
    response_model=list[CompanyResponse],
)
def list_companies(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    return db.query(Company).all()





@router.get(
    "/companies/{company_id}",
    response_model=CompanyResponse,
)
def get_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    company = (
        db.query(Company)
        .filter(Company.id == company_id)
        .first()
    )

    if company is None:
        raise HTTPException(
            status_code=404,
            detail="Company not found",
        )

    return company





@router.get(
    "/users",
    response_model=list[AdminUserListItem],
)
def list_users(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    return db.query(User).all()





@router.get(
    "/vehicles",
    response_model=list[VehicleResponse],
)
def list_all_vehicles(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    return db.query(Vehicle).all()





@router.post(
    "/vehicles/{vehicle_id}/force-deactivate",
    response_model=VehicleResponse,
)
def force_deactivate_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):

    vehicle = (
        db.query(Vehicle)
        .filter(Vehicle.id == vehicle_id)
        .first()
    )

    if vehicle is None:
        raise HTTPException(
            status_code=404,
            detail="Vehicle not found",
        )

    if not vehicle.is_active:
        raise HTTPException(
            status_code=409,
            detail="Vehicle is not activated",
        )

    vehicle.user_id = None
    vehicle.company_id = None
    vehicle.device_id = None
    vehicle.is_active = False

    db.commit()
    db.refresh(vehicle)

    return vehicle





@router.get(
    "/devices",
    response_model=list[DeviceResponse],
)
def list_all_devices(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    return db.query(Device).all()