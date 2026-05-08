"""
Admin-service — read-only mirror models for tables owned by other services.
These exist only so admin-service can query them for reporting/leaderboard purposes.
"""
import enum
import uuid
from decimal import Decimal

from sqlalchemy import Numeric, String, Integer, Boolean, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class Order(Base):
    """Mirror of orders table owned by order-service — read-only."""
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    symbol: Mapped[str] = mapped_column(String)
    side: Mapped[str] = mapped_column(String)
    market_type: Mapped[str] = mapped_column(String)
    order_type: Mapped[str] = mapped_column(String)
    quantity: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    price: Mapped[Decimal | None] = mapped_column(Numeric(20, 8), nullable=True)
    fill_price: Mapped[Decimal | None] = mapped_column(Numeric(20, 8), nullable=True)
    status: Mapped[str] = mapped_column(String)
    created_at: Mapped[str] = mapped_column(server_default=text("now()"))


class SimulationWallet(Base):
    """Mirror of simulation_wallets table owned by wallet-service — read-only."""
    __tablename__ = "simulation_wallets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    currency: Mapped[str] = mapped_column(String(20))
    balance: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    available_balance: Mapped[Decimal] = mapped_column(Numeric(20, 8))


class FuturesPosition(Base):
    """Mirror of futures_positions table owned by order-service — read-only."""
    __tablename__ = "futures_positions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    symbol: Mapped[str] = mapped_column(String)
    side: Mapped[str] = mapped_column(String)
    quantity: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    entry_price: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    realised_pnl: Mapped[Decimal | None] = mapped_column(Numeric(20, 8), nullable=True)
    status: Mapped[str] = mapped_column(String)
    created_at: Mapped[str] = mapped_column(server_default=text("now()"))
