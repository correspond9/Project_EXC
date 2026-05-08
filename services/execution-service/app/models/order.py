"""Mirror ORM models for tables owned by order-service.
Execution-service reads and updates these rows but does NOT own the migrations.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Numeric, String, Boolean, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    OPEN = "OPEN"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class OrderSide(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, enum.Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT = "TAKE_PROFIT"


class MarketType(str, enum.Enum):
    SPOT = "SPOT"
    FUTURES = "FUTURES"


class ExecutionMode(str, enum.Enum):
    SIMULATION = "SIMULATION"
    LIVE = "LIVE"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    side: Mapped[OrderSide] = mapped_column(SAEnum(OrderSide, name="order_side", create_type=False))
    order_type: Mapped[OrderType] = mapped_column(SAEnum(OrderType, name="order_type", create_type=False))
    market_type: Mapped[MarketType] = mapped_column(SAEnum(MarketType, name="market_type", create_type=False))
    quantity: Mapped[Decimal] = mapped_column(Numeric(28, 8))
    price: Mapped[Decimal | None] = mapped_column(Numeric(28, 8), nullable=True)
    stop_price: Mapped[Decimal | None] = mapped_column(Numeric(28, 8), nullable=True)
    status: Mapped[OrderStatus] = mapped_column(SAEnum(OrderStatus, name="order_status", create_type=False))
    execution_mode: Mapped[ExecutionMode] = mapped_column(
        SAEnum(ExecutionMode, name="execution_mode", create_type=False)
    )
    external_order_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    leverage: Mapped[int | None] = mapped_column(nullable=True)
    reduce_only: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class OrderFill(Base):
    __tablename__ = "order_fills"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    fill_price: Mapped[Decimal] = mapped_column(Numeric(28, 8), nullable=False)
    fill_quantity: Mapped[Decimal] = mapped_column(Numeric(28, 8), nullable=False)
    fee: Mapped[Decimal] = mapped_column(Numeric(28, 8), nullable=False, server_default="0")
    fee_currency: Mapped[str] = mapped_column(String(10), nullable=False, server_default="USDT")
    execution_mode: Mapped[ExecutionMode] = mapped_column(
        SAEnum(ExecutionMode, name="execution_mode", create_type=False),
        nullable=False,
        server_default="LIVE",
    )
    filled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
