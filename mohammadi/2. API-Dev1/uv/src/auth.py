import hashlib
import secrets
import jwt
from jwt.exceptions import InvalidTokenError
from datetime import datetime, timedelta, timezone
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
from .models import Admin, Company, Device, User, RefreshToken






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






def _hash_refresh_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


def issue_refresh_token(db: Session, role: str, subject_id: int) -> str:
    raw_token = secrets.token_urlsafe(48)

    record = RefreshToken(
        token_hash=_hash_refresh_token(raw_token),
        role=role,
        subject_id=subject_id,
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )

    db.add(record)
    db.commit()

    return raw_token


def rotate_refresh_token(db: Session, raw_token: str) -> tuple[str, str, int]:

    invalid_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token",
    )

    token_hash = _hash_refresh_token(raw_token)

    record = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == token_hash)
        .first()
    )

    if record is None or record.revoked:
        raise invalid_exception

    if record.expires_at < datetime.now(timezone.utc):
        raise invalid_exception

    record.revoked = True
    db.commit()

    if record.role == "user":
        subject = db.query(User).filter(User.id == record.subject_id).first()
        username = subject.mobile if subject else None
    else:
        subject = db.query(Company).filter(Company.id == record.subject_id).first()
        username = subject.username if subject else None

    if subject is None:
        raise invalid_exception

    new_access_token = create_access_token(
        subject_id=record.subject_id,
        role=record.role,
        username=username,
    )

    new_refresh_token = issue_refresh_token(db, record.role, record.subject_id)

    return new_access_token, new_refresh_token, record.role


def revoke_refresh_token(db: Session, raw_token: str) -> None:
    token_hash = _hash_refresh_token(raw_token)

    record = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == token_hash)
        .first()
    )

    if record is not None:
        record.revoked = True
        db.commit()




def get_current_admin_or_company(
    payload: dict = Depends(get_token_payload),
    db: Session = Depends(get_db),
) -> tuple[str, "Admin | Company"]:

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