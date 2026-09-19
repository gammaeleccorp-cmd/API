from datetime import datetime, timedelta, timezone

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session


from ..auth import (
    get_current_command_issuer,
    get_current_device,
    get_current_owner,
    get_current_owner_or_admin,
    get_current_user,
)
from ..database import get_db

from ..models import (
    Device,
    DeviceCommand,
    User,
    Vehicle,
)

from ..schemas import (
    DeviceCommandCreate,
    DeviceCommandResponse,
    DeviceCreate,
    DeviceHealthResponse,
    DeviceResponse,
    MyDeviceResponse,
)





HEALTH_TIMEOUT = timedelta(minutes=2)





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





def _find_device_by_serial(db: Session, serial: str) -> Device:
    """
    Existence check ONLY - no ownership check. Raises 404 if no device
    at all has this serial.
    """

    device = db.query(Device).filter(Device.serial == serial).first()

    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")

    return device


def _authorize_owner(device: Device, role: str, owner) -> Device:
    """
    Raises 403 if the device exists but does not belong to this
    user/company. Admin always passes.
    """

    if role == "admin":
        return device

    if role == "user" and device.owner_user_id != owner.id:
        raise HTTPException(status_code=403, detail="You do not own this device")

    if role == "company" and device.owner_company_id != owner.id:
        raise HTTPException(
            status_code=403,
            detail="Your company does not own this device",
        )

    return device


def _get_owned_device(db: Session, role: str, owner, serial: str) -> Device:
    device = _find_device_by_serial(db, serial)
    return _authorize_owner(device, role, owner)


def _authorize_issuer(device: Device, role: str, issuer) -> Device:
    """
    Only company ownership restricts command creation - admin may
    issue a command to any device.
    """

    if role == "company" and device.owner_company_id != issuer.id:
        raise HTTPException(
            status_code=403,
            detail="Your company does not own this device",
        )

    return device


def _verify_device_token_serial(
    db: Session,
    serial: str,
    token_device: Device,
) -> Device:
    """
    404 if no device with this serial exists at all; 403 if it exists
    but is not the device that owns the presented token.
    """

    device = _find_device_by_serial(db, serial)

    if device.id != token_device.id:
        raise HTTPException(
            status_code=403,
            detail="Device token does not match this serial",
        )

    return device


def _is_online(last_heartbeat_at: datetime | None) -> bool:

    if last_heartbeat_at is None:
        return False

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    last = last_heartbeat_at.replace(tzinfo=None)

    return (now - last) <= HEALTH_TIMEOUT





# ===== Heartbeat & Health =====

@router.post(
    "/{serial}/heartbeat",
    response_model=DeviceHealthResponse,
)
def send_heartbeat(
    serial: str,
    db: Session = Depends(get_db),
    device: Device = Depends(get_current_device),
):

    _verify_device_token_serial(db, serial, device)

    device.last_heartbeat_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(device)

    return {
        "serial": device.serial,
        "online": True,
        "last_heartbeat_at": device.last_heartbeat_at,
    }





@router.get(
    "/{serial}/health",
    response_model=DeviceHealthResponse,
)
def get_device_health(
    serial: str,
    db: Session = Depends(get_db),
    current_owner: tuple = Depends(get_current_owner),
):

    role, owner = current_owner
    device = _get_owned_device(db, role, owner, serial)

    return {
        "serial": device.serial,
        "online": _is_online(device.last_heartbeat_at),
        "last_heartbeat_at": device.last_heartbeat_at,
    }





# ===== Commands =====

@router.post(
    "/{serial}/commands",
    response_model=DeviceCommandResponse,
    status_code=201,
)
def send_command(
    serial: str,
    data: DeviceCommandCreate,
    db: Session = Depends(get_db),
    current_issuer: tuple = Depends(get_current_command_issuer),
):

    role, issuer = current_issuer
    device = _find_device_by_serial(db, serial)
    _authorize_issuer(device, role, issuer)

    command = DeviceCommand(
        device_id=device.id,
        command=data.command,
        status="pending",
    )

    db.add(command)
    db.commit()
    db.refresh(command)

    return command





@router.get(
    "/{serial}/commands/pending",
    response_model=list[DeviceCommandResponse],
)
def get_pending_commands(
    serial: str,
    db: Session = Depends(get_db),
    device: Device = Depends(get_current_device),
):

    _verify_device_token_serial(db, serial, device)

    pending_commands = (
        db.query(DeviceCommand)
        .filter(
            DeviceCommand.device_id == device.id,
            DeviceCommand.status == "pending",
        )
        .all()
    )

    # A command is only ever handed out as "pending" once: as soon as
    # the device picks it up here, it moves to "delivered" so a
    # repeated poll does not receive the same command again.
    for command in pending_commands:
        command.status = "delivered"
        command.delivered_at = datetime.now(timezone.utc)

    db.commit()

    for command in pending_commands:
        db.refresh(command)

    return pending_commands





@router.post(
    "/{serial}/commands/{command_id}/ack",
    response_model=DeviceCommandResponse,
)
def acknowledge_command(
    serial: str,
    command_id: int,
    db: Session = Depends(get_db),
    device: Device = Depends(get_current_device),
):

    _verify_device_token_serial(db, serial, device)

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

    if command.status != "delivered":
        raise HTTPException(
            status_code=409,
            detail="Command has not been delivered yet",
        )

    command.status = "acknowledged"
    command.acknowledged_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(command)

    return command





@router.get(
    "/{serial}/commands/{command_id}",
    response_model=DeviceCommandResponse,
)
def get_command(
    serial: str,
    command_id: int,
    db: Session = Depends(get_db),
    current_owner: tuple = Depends(get_current_owner_or_admin),
):

    role, owner = current_owner
    device = _get_owned_device(db, role, owner, serial)

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
