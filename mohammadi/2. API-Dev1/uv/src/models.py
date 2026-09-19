from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from .database import Base






def utc_now() -> datetime:
    return datetime.now(timezone.utc)





class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    mobile: Mapped[str] = mapped_column(
        String(11),
        unique=True,
        nullable=False,
        index=True,
    )

    national_id: Mapped[str] = mapped_column(
        String(10),
        unique=True,
        nullable=False,
        index=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),  
        default=utc_now,          
        nullable=False,
    )

    vehicles: Mapped[list["Vehicle"]] = relationship(
        back_populates="user",
    )





class Admin(Base):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),  
        default=utc_now,          
        nullable=False,
    )





class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),  
        default=utc_now,          
        nullable=False,
    )

    vehicles: Mapped[list["Vehicle"]] = relationship(
        back_populates="company",
    )





class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    token_hash: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True,
    )

    role: Mapped[str] = mapped_column(String(20), nullable=False)

    subject_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )

    revoked: Mapped[bool] = mapped_column(default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False,
    )
    




class Device(Base):
    __tablename__ = "devices"

    __table_args__ = (
        CheckConstraint(
            "("
            "(owner_user_id IS NOT NULL AND owner_company_id IS NULL) OR "
            "(owner_user_id IS NULL AND owner_company_id IS NOT NULL)"
            ")",
            name="ck_device_single_owner",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    serial: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    owner_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    owner_company_id: Mapped[int | None] = mapped_column(
        ForeignKey("companies.id"),
        nullable=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),  
        default=utc_now,          
        nullable=False,
    )

    owner_user: Mapped["User | None"] = relationship()
    owner_company: Mapped["Company | None"] = relationship()

    vehicle: Mapped["Vehicle | None"] = relationship(
        back_populates="device",
        uselist=False,
    )

    last_heartbeat_at: Mapped[datetime | None] = mapped_column(
    DateTime(timezone=True),
    nullable=True,
    )



class Vehicle(Base):
    __tablename__ = "vehicles"

    __table_args__ = (
        CheckConstraint(
            "(user_id IS NULL OR company_id IS NULL)",
            name="ck_vehicle_single_owner_type",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    vin: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    company_id: Mapped[int | None] = mapped_column(
        ForeignKey("companies.id"),
        nullable=True,
        index=True,
    )

    device_id: Mapped[int | None] = mapped_column(
        ForeignKey("devices.id"),
        unique=True,
        nullable=True,
        index=True,
    )

    is_active: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )

    activated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),  
        default=utc_now,          
        nullable=False,
    )

    user: Mapped["User | None"] = relationship(
        back_populates="vehicles",
    )

    company: Mapped["Company | None"] = relationship(
        back_populates="vehicles",
    )

    device: Mapped["Device | None"] = relationship(
        back_populates="vehicle",
    )

    telemetry: Mapped[list["Telemetry"]] = relationship(
        back_populates="vehicle",
    )





class Telemetry(Base):
    __tablename__ = "telemetry"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id"),
        nullable=False,
        index=True,
    )

    vehicle_id: Mapped[int] = mapped_column(
        ForeignKey("vehicles.id"),
        nullable=False,
        index=True,
    )

    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    speed: Mapped[float | None] = mapped_column(Float, nullable=True)
    rpm: Mapped[float | None] = mapped_column(Float, nullable=True)
    fuel_level: Mapped[float | None] = mapped_column(Float, nullable=True)

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),  
        default=utc_now,          
        nullable=False,
    )

    vehicle: Mapped["Vehicle"] = relationship(
        back_populates="telemetry",
    )





class DeviceCommand(Base):
    __tablename__ = "device_commands"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id"),
        nullable=False,
        index=True,
    )

    command_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
    )

    issued_by_role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    issued_by_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    device: Mapped["Device"] = relationship()