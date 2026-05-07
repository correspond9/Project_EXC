import enum
import uuid
from decimal import Decimal

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Numeric, String, func
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
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    side: Mapped[OrderSide] = mapped_column(
        SAEnum(OrderSide, name="order_side"), nullable=False
    )
    order_type: Mapped[OrderType] = mapped_column(
        SAEnum(OrderType, name="order_type"), nullable=False
    )
    market_type: Mapped[MarketType] = mapped_column(
        SAEnum(MarketType, name="market_type_order"), nullable=False, server_default="SPOT"
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(28, 8), nullable=False)
    price: Mapped[Decimal | None] = mapped_column(Numeric(28, 8), nullable=True)
    status: Mapped[OrderStatus] = mapped_column(
        SAEnum(OrderStatus, name="order_status"),
        nullable=False,
        server_default="PENDING",
    )
    execution_mode: Mapped[ExecutionMode] = mapped_column(
        SAEnum(ExecutionMode, name="execution_mode"),
        nullable=False,
        server_default="SIMULATION",
    )
    external_order_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    created_at: Mapped[str] = mapped_column(server_default=func.now())
    updated_at: Mapped[str] = mapped_column(server_default=func.now(), onupdate=func.now())

    fills: Mapped[list["OrderFill"]] = relationship(
        "OrderFill", back_populates="order", lazy="selectin"
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
        SAEnum(ExecutionMode, name="execution_mode"), nullable=False
    )
    filled_at: Mapped[str] = mapped_column(server_default=func.now())

    order: Mapped["Order"] = relationship("Order", back_populates="fills")
