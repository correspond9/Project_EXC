"""
Options ORM models — read/write for options_contracts and options_positions tables.
"""
import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Enum as SAEnum, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class OptionType(str, enum.Enum):
    CALL = "CALL"
    PUT = "PUT"


class OptionsPositionStatus(str, enum.Enum):
    OPEN = "OPEN"
    EXPIRED_ITM = "EXPIRED_ITM"   # In the money — settled with payout
    EXPIRED_OTM = "EXPIRED_OTM"   # Out of the money — expired worthless


class OptionsContract(Base):
    __tablename__ = "options_contracts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    underlying_symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    option_type: Mapped[OptionType] = mapped_column(
        SAEnum(OptionType, name="option_type", create_constraint=True), nullable=False
    )
    strike_price: Mapped[Decimal] = mapped_column(Numeric(28, 8), nullable=False)
    expiry_date: Mapped[date] = mapped_column(Date, nullable=False)
    implied_volatility: Mapped[Decimal] = mapped_column(
        Numeric(10, 6), nullable=False, server_default="0.60"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class OptionsPosition(Base):
    __tablename__ = "options_positions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    contract_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    # Denormalised for easy settlement without joins
    underlying_symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    option_type: Mapped[OptionType] = mapped_column(
        SAEnum(OptionType, name="option_type", create_constraint=False), nullable=False
    )
    strike_price: Mapped[Decimal] = mapped_column(Numeric(28, 8), nullable=False)
    expiry_date: Mapped[date] = mapped_column(Date, nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(28, 8), nullable=False)
    premium_paid: Mapped[Decimal] = mapped_column(Numeric(28, 8), nullable=False)
    settlement_price: Mapped[Decimal | None] = mapped_column(Numeric(28, 8), nullable=True)
    payout: Mapped[Decimal | None] = mapped_column(Numeric(28, 8), nullable=True)
    status: Mapped[OptionsPositionStatus] = mapped_column(
        SAEnum(OptionsPositionStatus, name="options_position_status", create_constraint=True),
        nullable=False,
        server_default="OPEN",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    settled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
