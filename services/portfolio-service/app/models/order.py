"""Read-only mirror of orders + order_fills (owned by order-service)."""
import uuid
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class OrderReadOnly(Base):
    """Read-only view of the orders table owned by order-service."""
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    symbol: Mapped[str] = mapped_column(sa.String(20), nullable=False)
    side: Mapped[str] = mapped_column(sa.Enum("BUY", "SELL", name="order_side", create_type=False), nullable=False)
    order_type: Mapped[str] = mapped_column(sa.Enum("MARKET", "LIMIT", "STOP_LOSS", "TAKE_PROFIT", name="order_type", create_type=False), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(sa.Numeric(28, 8), nullable=False)
    price: Mapped[Decimal | None] = mapped_column(sa.Numeric(28, 8), nullable=True)
    stop_price: Mapped[Decimal | None] = mapped_column(sa.Numeric(28, 8), nullable=True)
    status: Mapped[str] = mapped_column(sa.Enum("PENDING", "OPEN", "PARTIALLY_FILLED", "FILLED", "CANCELLED", "REJECTED", name="order_status", create_type=False), nullable=False)
    execution_mode: Mapped[str] = mapped_column(sa.Enum("SIMULATION", "LIVE", name="execution_mode", create_type=False), nullable=False)
    created_at: Mapped[sa.DateTime] = mapped_column(sa.DateTime(timezone=True))
    updated_at: Mapped[sa.DateTime] = mapped_column(sa.DateTime(timezone=True))

    fills: Mapped[list["OrderFillReadOnly"]] = relationship(
        "OrderFillReadOnly", back_populates="order", lazy="selectin"
    )


class OrderFillReadOnly(Base):
    """Read-only view of the order_fills table owned by order-service."""
    __tablename__ = "order_fills"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("orders.id"),
        nullable=False,
    )
    fill_price: Mapped[Decimal] = mapped_column(sa.Numeric(28, 8), nullable=False)
    fill_quantity: Mapped[Decimal] = mapped_column(sa.Numeric(28, 8), nullable=False)
    fee: Mapped[Decimal] = mapped_column(sa.Numeric(28, 8), nullable=False)
    fee_currency: Mapped[str] = mapped_column(sa.String(10), nullable=False)
    execution_mode: Mapped[str] = mapped_column(sa.Enum("SIMULATION", "LIVE", name="execution_mode", create_type=False), nullable=False)

    order: Mapped["OrderReadOnly"] = relationship("OrderReadOnly", back_populates="fills")
