"""
SQLAlchemy models that mirror the orders / order_fills tables owned by order-service.
The simulation engine shares the same PostgreSQL database and writes directly to
these tables (fills, status updates).  No Alembic migrations here — schema changes
are owned by order-service's migration set.
"""
import enum
import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


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
    OPTIONS = "OPTIONS"


class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    OPEN = "OPEN"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class ExecutionMode(str, enum.Enum):
    SIMULATION = "SIMULATION"
    LIVE = "LIVE"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    symbol: Mapped[str] = mapped_column(sa.String(20), nullable=False)
    side: Mapped[OrderSide] = mapped_column(
        sa.Enum("BUY", "SELL", name="order_side", create_type=False), nullable=False
    )
    order_type: Mapped[OrderType] = mapped_column(
        sa.Enum("MARKET", "LIMIT", "STOP_LOSS", "TAKE_PROFIT", name="order_type", create_type=False),
        nullable=False,
    )
    market_type: Mapped[MarketType] = mapped_column(
        sa.Enum("SPOT", "FUTURES", "OPTIONS", name="market_type_order", create_type=False),
        nullable=False,
        server_default="SPOT",
    )
    quantity: Mapped[sa.Numeric] = mapped_column(sa.Numeric(28, 8), nullable=False)
    price: Mapped[sa.Numeric | None] = mapped_column(sa.Numeric(28, 8), nullable=True)
    stop_price: Mapped[sa.Numeric | None] = mapped_column(sa.Numeric(28, 8), nullable=True)
    status: Mapped[OrderStatus] = mapped_column(
        sa.Enum(
            "PENDING", "OPEN", "PARTIALLY_FILLED", "FILLED", "CANCELLED", "REJECTED",
            name="order_status",
            create_type=False,
        ),
        nullable=False,
        server_default="PENDING",
    )
    execution_mode: Mapped[ExecutionMode] = mapped_column(
        sa.Enum("SIMULATION", "LIVE", name="execution_mode", create_type=False),
        nullable=False,
        server_default="SIMULATION",
    )
    external_order_id: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    created_at: Mapped[sa.DateTime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.text("now()")
    )
    updated_at: Mapped[sa.DateTime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.text("now()")
    )

    fills: Mapped[list["OrderFill"]] = relationship("OrderFill", back_populates="order")


class OrderFill(Base):
    __tablename__ = "order_fills"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    fill_price: Mapped[sa.Numeric] = mapped_column(sa.Numeric(28, 8), nullable=False)
    fill_quantity: Mapped[sa.Numeric] = mapped_column(sa.Numeric(28, 8), nullable=False)
    fee: Mapped[sa.Numeric] = mapped_column(sa.Numeric(28, 8), nullable=False, server_default="0")
    fee_currency: Mapped[str] = mapped_column(sa.String(10), nullable=False, server_default="USDT")
    execution_mode: Mapped[ExecutionMode] = mapped_column(
        sa.Enum("SIMULATION", "LIVE", name="execution_mode", create_type=False), nullable=False
    )
    filled_at: Mapped[sa.DateTime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.text("now()")
    )

    order: Mapped["Order"] = relationship("Order", back_populates="fills")
