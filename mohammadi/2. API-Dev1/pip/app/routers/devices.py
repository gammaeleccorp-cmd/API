from datetime import datetime, timedelta, timezone
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlalchemy.orm import Session
from ..auth import (
    get_current_admin_or_company,
    get_current_device,
    get_current_user,
)
from ..database import get_db
from ..models import (
    Device,
    DeviceCommand,
    User,
)
from ..schemas import (
    CommandCreate,
    CommandResponse,
    DeviceCreate,
    DeviceResponse,
    HealthResponse,
    MyDeviceResponse,
)





router = APIRouter(
    prefix="/devices",
    tags=["Devices"],
)

HEARTBEAT_TIMEOUT_SECONDS = 120

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
        raise HTTPException(
            status_code=409,
            detail="Device already exists",
        )

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





def _get_device_or_404(db: Session, serial: str) -> Device:
    device = db.query(Device).filter(Device.serial == serial).first()
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


def _assert_can_view_device(device: Device, role: str, subject_id: int) -> None:
    if role == "admin":
        return
    if role == "user" and device.owner_user_id == subject_id:
        return
    if role == "company" and device.owner_company_id == subject_id:
        return
    raise HTTPException(status_code=403, detail="You do not have access to this device")


def _compute_online(device: Device) -> bool:
    if device.last_heartbeat_at is None:
        return False
    last_heartbeat = device.last_heartbeat_at
    if last_heartbeat.tzinfo is None:
        last_heartbeat = last_heartbeat.replace(tzinfo=timezone.utc)
    age = datetime.now(timezone.utc) - last_heartbeat
    return age <= timedelta(seconds=HEARTBEAT_TIMEOUT_SECONDS)



@router.post(
    "/{serial}/heartbeat",
    status_code=204,
)
def send_heartbeat(
    serial: str,
    db: Session = Depends(get_db),
    device: Device = Depends(get_current_device),
):

    if device.serial != serial:
        raise HTTPException(
            status_code=403,
            detail="Token does not belong to this device",
        )

    device.last_heartbeat_at = datetime.now(timezone.utc)

    db.commit()

    return None



@router.get(
    "/{serial}/health",
    response_model=HealthResponse,
)
def get_device_health(
    serial: str,
    db: Session = Depends(get_db),
    owner: tuple = Depends(get_current_admin_or_company),
):

    role, subject = owner

    device = _get_device_or_404(db, serial)
    _assert_can_view_device(device, role, subject.id)

    return {
        "serial": device.serial,
        "online": _compute_online(device),
        "last_heartbeat_at": device.last_heartbeat_at,
    }



ACTIVE_STATUSES = ("pending", "delivered")


@router.post(
    "/{serial}/commands",
    response_model=CommandResponse,
    status_code=201,
)
def create_command(
    serial: str,
    data: CommandCreate,
    db: Session = Depends(get_db),
    issuer: tuple = Depends(get_current_admin_or_company),
):

    role, subject = issuer

    device = _get_device_or_404(db, serial)

    if role == "company" and device.owner_company_id != subject.id:
        raise HTTPException(
            status_code=403,
            detail="Your company does not own this device",
        )

    duplicate = (
        db.query(DeviceCommand)
        .filter(
            DeviceCommand.device_id == device.id,
            DeviceCommand.command_type == data.command_type,
            DeviceCommand.status.in_(ACTIVE_STATUSES),
        )
        .first()
    )

    if duplicate is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                f"A '{data.command_type}' command is already "
                "pending or delivered for this device"
            ),
        )

    command = DeviceCommand(
        device_id=device.id,
        command_type=data.command_type,
        status="pending",
        issued_by_role=role,
        issued_by_id=subject.id,
    )

    db.add(command)
    db.commit()
    db.refresh(command)

    return command


@router.get(
    "/{serial}/commands/pending",
    response_model=list[CommandResponse],
)
def get_pending_commands(
    serial: str,
    db: Session = Depends(get_db),
    device: Device = Depends(get_current_device),
):

    if device.serial != serial:
        raise HTTPException(
            status_code=403,
            detail="Token does not belong to this device",
        )

    pending_commands = (
        db.query(DeviceCommand)
        .filter(
            DeviceCommand.device_id == device.id,
            DeviceCommand.status == "pending",
        )
        .all()
    )

    now = datetime.now(timezone.utc)

    for command in pending_commands:
        command.status = "delivered"
        command.delivered_at = now

    db.commit()

    for command in pending_commands:
        db.refresh(command)

    return pending_commands


@router.post(
    "/{serial}/commands/{command_id}/ack",
    response_model=CommandResponse,
)
def acknowledge_command(
    serial: str,
    command_id: int,
    db: Session = Depends(get_db),
    device: Device = Depends(get_current_device),
):

    if device.serial != serial:
        raise HTTPException(
            status_code=403,
            detail="Token does not belong to this device",
        )

    command = (
        db.query(DeviceCommand)
        .filter(DeviceCommand.id == command_id)
        .first()
    )

    if command is None:
        raise HTTPException(status_code=404, detail="Command not found")

    if command.device_id != device.id:
        raise HTTPException(
            status_code=403,
            detail="This command does not belong to your device",
        )

    if command.status != "delivered":
        raise HTTPException(
            status_code=409,
            detail=f"Command cannot be acknowledged from status '{command.status}'",
        )

    command.status = "acknowledged"
    command.acknowledged_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(command)

    return command


@router.get(
    "/{serial}/commands/{command_id}",
    response_model=CommandResponse,
)
def get_command(
    serial: str,
    command_id: int,
    db: Session = Depends(get_db),
    owner: tuple = Depends(get_current_admin_or_company),
):

    role, subject = owner

    device = _get_device_or_404(db, serial)
    _assert_can_view_device(device, role, subject.id)

    command = (
        db.query(DeviceCommand)
        .filter(
            DeviceCommand.id == command_id,
            DeviceCommand.device_id == device.id,
        )
        .first()
    )

    if command is None:
        raise HTTPException(status_code=404, detail="Command not found")

    return command