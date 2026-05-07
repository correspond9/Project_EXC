"""
Read-only ORM models for tables owned by user-service.
Admin-service never runs migrations for these — they are created by user-service.
These models exist only so admin-service can query them via SQLAlchemy.
"""
import enum
import uuid

from sqlalchemy import Boolean, Enum as SAEnum, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class UserRole(str, enum.Enum):
    STUDENT = "STUDENT"
    TRADER = "TRADER"
    ADMIN = "ADMIN"
    SUPER_ADMIN = "SUPER_ADMIN"


class TradingMode(str, enum.Enum):
    SIMULATION = "SIMULATION"
    LIVE = "LIVE"


class KYCStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class User(Base):
    """Mirror of the users table owned by user-service — read-only in admin-service."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    email: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole, name="userrole", create_type=False))
    trading_mode: Mapped[TradingMode] = mapped_column(
        SAEnum(TradingMode, name="tradingmode", create_type=False)
    )
    kyc_status: Mapped[KYCStatus] = mapped_column(
        SAEnum(KYCStatus, name="kycstatus", create_type=False)
    )
    is_active: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[str] = mapped_column(server_default=func.now())
    updated_at: Mapped[str] = mapped_column(server_default=func.now())
