"""Read-only ORM mirrors for futures tables (positions + margin_accounts)."""
import enum
import uuid
from decimal import Decimal

from sqlalchemy import Enum as SAEnum, Integer, Numeric, String, UniqueConstraint
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class PositionSide(str, enum.Enum):
    LONG = "LONG"
    SHORT = "SHORT"


class PositionStatus(str, enum.Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    LIQUIDATED = "LIQUIDATED"


class FuturesExecutionMode(str, enum.Enum):
    SIMULATION = "SIMULATION"
    LIVE = "LIVE"


class MarginAccount(Base):
    __tablename__ = "margin_accounts"
    __table_args__ = (
        UniqueConstraint("user_id", "execution_mode", name="uq_margin_user_mode"),
        {"extend_existing": True},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    execution_mode: Mapped[FuturesExecutionMode] = mapped_column(
        SAEnum(FuturesExecutionMode, name="execution_mode", create_constraint=False),
        nullable=False,
    )
    total_margin_balance: Mapped[Decimal] = mapped_column(Numeric(28, 8), nullable=False)
    available_margin: Mapped[Decimal] = mapped_column(Numeric(28, 8), nullable=False)
    used_margin: Mapped[Decimal] = mapped_column(Numeric(28, 8), nullable=False)
    updated_at: Mapped[str] = mapped_column(nullable=True)


class Position(Base):
    __tablename__ = "positions"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    order_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    side: Mapped[PositionSide] = mapped_column(
        SAEnum(PositionSide, name="position_side", create_constraint=False),
        nullable=False,
    )
    execution_mode: Mapped[FuturesExecutionMode] = mapped_column(
        SAEnum(FuturesExecutionMode, name="execution_mode", create_constraint=False),
        nullable=False,
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(28, 8), nullable=False)
    entry_price: Mapped[Decimal] = mapped_column(Numeric(28, 8), nullable=False)
    leverage: Mapped[int] = mapped_column(Integer, nullable=False)
    margin: Mapped[Decimal] = mapped_column(Numeric(28, 8), nullable=False)
    liquidation_price: Mapped[Decimal] = mapped_column(Numeric(28, 8), nullable=False)
    unrealised_pnl: Mapped[Decimal] = mapped_column(Numeric(28, 8), nullable=False)
    realised_pnl: Mapped[Decimal | None] = mapped_column(Numeric(28, 8), nullable=True)
    closed_price: Mapped[Decimal | None] = mapped_column(Numeric(28, 8), nullable=True)
    status: Mapped[PositionStatus] = mapped_column(
        SAEnum(PositionStatus, name="position_status", create_constraint=False),
        nullable=False,
    )
    created_at: Mapped[str] = mapped_column(nullable=True)
    closed_at: Mapped[str | None] = mapped_column(nullable=True)
