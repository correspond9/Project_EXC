"""ORM models for risk-related tables owned by this service."""
import uuid
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class MarginCall(Base):
    __tablename__ = "margin_calls"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    position_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    margin_ratio_at_call: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    price_at_call: Mapped[Decimal] = mapped_column(Numeric(28, 8), nullable=False)
    created_at: Mapped[str] = mapped_column(server_default=func.now())
    resolved_at: Mapped[str | None] = mapped_column(nullable=True)


class Liquidation(Base):
    __tablename__ = "liquidations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    position_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    liquidation_price: Mapped[Decimal] = mapped_column(Numeric(28, 8), nullable=False)
    realised_pnl: Mapped[Decimal] = mapped_column(Numeric(28, 8), nullable=False)
    created_at: Mapped[str] = mapped_column(server_default=func.now())
