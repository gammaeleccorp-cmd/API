from datetime import datetime, timedelta, timezone

import jwt
from jwt.exceptions import InvalidTokenError

from fastapi import (
    Depends,
    HTTPException,
    status,
)

from fastapi.security import OAuth2PasswordBearer

from pwdlib import PasswordHash

from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .models import Admin, Company, Device, User




password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(
    password: str,
    hashed_password: str,
) -> bool:

    return password_hash.verify(
        password,
        hashed_password,
    )


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)



def create_access_token(
    subject_id: int,
    role: str,
    username: str,
    expire_minutes: int | None = None,
    no_expiry: bool = False,
) -> str:

    payload = {
        "sub": str(subject_id),
        "role": role,
        "username": username,
    }

    if not no_expiry:
        if expire_minutes is None:
            expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES

        expire = (
            datetime.now(timezone.utc)
            + timedelta(minutes=expire_minutes)
        )

        payload["exp"] = expire

    token = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    return token


def _decode_token(token: str) -> dict:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
    except InvalidTokenError:
        raise credentials_exception

    if payload.get("sub") is None or payload.get("role") is None:
        raise credentials_exception

    return payload


def get_token_payload(
    token: str = Depends(oauth2_scheme),
) -> dict:
    return _decode_token(token)


def get_current_user(
    payload: dict = Depends(get_token_payload),
    db: Session = Depends(get_db),
) -> User:

    forbidden_exception = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="This action requires a user account",
    )

    if payload.get("role") != "user":
        raise forbidden_exception

    try:
        user_id = int(payload["sub"])
    except (ValueError, TypeError):
        raise forbidden_exception

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if user is None:
        raise forbidden_exception

    return user


def get_current_company(
    payload: dict = Depends(get_token_payload),
    db: Session = Depends(get_db),
) -> Company:

    forbidden_exception = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="This action requires a company account",
    )

    if payload.get("role") != "company":
        raise forbidden_exception

    try:
        company_id = int(payload["sub"])
    except (ValueError, TypeError):
        raise forbidden_exception

    company = (
        db.query(Company)
        .filter(Company.id == company_id)
        .first()
    )

    if company is None:
        raise forbidden_exception

    return company


def get_current_admin(
    payload: dict = Depends(get_token_payload),
    db: Session = Depends(get_db),
) -> Admin:

    forbidden_exception = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="This action requires an admin account",
    )

    if payload.get("role") != "admin":
        raise forbidden_exception

    try:
        admin_id = int(payload["sub"])
    except (ValueError, TypeError):
        raise forbidden_exception

    admin = (
        db.query(Admin)
        .filter(Admin.id == admin_id)
        .first()
    )

    if admin is None:
        raise forbidden_exception

    return admin


def get_current_owner(
    payload: dict = Depends(get_token_payload),
    db: Session = Depends(get_db),
) -> tuple[str, "User | Company"]:

    forbidden_exception = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="This action requires a user or company account",
    )

    role = payload.get("role")

    if role not in ("user", "company"):
        raise forbidden_exception

    try:
        subject_id = int(payload["sub"])
    except (ValueError, TypeError):
        raise forbidden_exception

    if role == "user":
        owner = db.query(User).filter(User.id == subject_id).first()
    else:
        owner = db.query(Company).filter(Company.id == subject_id).first()

    if owner is None:
        raise forbidden_exception

    return role, owner


def get_current_command_issuer(
    payload: dict = Depends(get_token_payload),
    db: Session = Depends(get_db),
) -> tuple[str, "Admin | Company"]:
    """
    Only admin or company accounts may issue Device Commands.
    """

    forbidden_exception = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="This action requires an admin or company account",
    )

    role = payload.get("role")

    if role not in ("admin", "company"):
        raise forbidden_exception

    try:
        subject_id = int(payload["sub"])
    except (ValueError, TypeError):
        raise forbidden_exception

    if role == "admin":
        subject = db.query(Admin).filter(Admin.id == subject_id).first()
    else:
        subject = db.query(Company).filter(Company.id == subject_id).first()

    if subject is None:
        raise forbidden_exception

    return role, subject


def get_current_owner_or_admin(
    payload: dict = Depends(get_token_payload),
    db: Session = Depends(get_db),
) -> tuple[str, "User | Company | Admin"]:
    """
    A user/company may act on their own resources; an admin may act on
    any resource. Ownership is still enforced by the caller for the
    user/company cases.
    """

    forbidden_exception = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="This action requires a user, company or admin account",
    )

    role = payload.get("role")

    if role not in ("user", "company", "admin"):
        raise forbidden_exception

    try:
        subject_id = int(payload["sub"])
    except (ValueError, TypeError):
        raise forbidden_exception

    if role == "user":
        subject = db.query(User).filter(User.id == subject_id).first()
    elif role == "company":
        subject = db.query(Company).filter(Company.id == subject_id).first()
    else:
        subject = db.query(Admin).filter(Admin.id == subject_id).first()

    if subject is None:
        raise forbidden_exception

    return role, subject


def get_current_device(
    payload: dict = Depends(get_token_payload),
    db: Session = Depends(get_db),
) -> Device:

    forbidden_exception = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="This action requires a device token",
    )

    if payload.get("role") != "device":
        raise forbidden_exception

    try:
        device_id = int(payload["sub"])
    except (ValueError, TypeError):
        raise forbidden_exception

    device = (
        db.query(Device)
        .filter(Device.id == device_id)
        .first()
    )

    if device is None:
        raise forbidden_exception

    return device
