import enum
import uuid
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, Integer, Numeric, String, UniqueConstraint, func
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


class ExecutionMode(str, enum.Enum):
    SIMULATION = "SIMULATION"
    LIVE = "LIVE"


class MarginAccount(Base):
    __tablename__ = "margin_accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    execution_mode: Mapped[ExecutionMode] = mapped_column(
        SAEnum(ExecutionMode, name="execution_mode", create_constraint=False),
        nullable=False,
        server_default="SIMULATION",
    )
    total_margin_balance: Mapped[Decimal] = mapped_column(Numeric(28, 8), nullable=False, server_default="0")
    available_margin: Mapped[Decimal] = mapped_column(Numeric(28, 8), nullable=False, server_default="0")
    used_margin: Mapped[Decimal] = mapped_column(Numeric(28, 8), nullable=False, server_default="0")
    updated_at: Mapped[str] = mapped_column(server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "execution_mode", name="uq_margin_user_mode"),
    )


class Position(Base):
    __tablename__ = "positions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    order_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    side: Mapped[PositionSide] = mapped_column(
        SAEnum(PositionSide, name="position_side", create_constraint=False),
        nullable=False,
    )
    execution_mode: Mapped[ExecutionMode] = mapped_column(
        SAEnum(ExecutionMode, name="execution_mode", create_constraint=False),
        nullable=False,
        server_default="SIMULATION",
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(28, 8), nullable=False)
    entry_price: Mapped[Decimal] = mapped_column(Numeric(28, 8), nullable=False)
    leverage: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    margin: Mapped[Decimal] = mapped_column(Numeric(28, 8), nullable=False)
    liquidation_price: Mapped[Decimal] = mapped_column(Numeric(28, 8), nullable=False)
    unrealised_pnl: Mapped[Decimal] = mapped_column(Numeric(28, 8), nullable=False, server_default="0")
    realised_pnl: Mapped[Decimal | None] = mapped_column(Numeric(28, 8), nullable=True)
    closed_price: Mapped[Decimal | None] = mapped_column(Numeric(28, 8), nullable=True)
    status: Mapped[PositionStatus] = mapped_column(
        SAEnum(PositionStatus, name="position_status", create_constraint=False),
        nullable=False,
        server_default="OPEN",
    )
    created_at: Mapped[str] = mapped_column(server_default=func.now())
    closed_at: Mapped[str | None] = mapped_column(nullable=True)


class UserPositionLimit(Base):
    __tablename__ = "user_position_limits"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, unique=True)
    max_position_value_usdt: Mapped[Decimal] = mapped_column(
        Numeric(28, 8), nullable=False, server_default="50000"
    )
    updated_at: Mapped[str | None] = mapped_column(nullable=True)
