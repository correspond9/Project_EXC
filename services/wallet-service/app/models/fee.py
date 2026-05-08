"""FeeLedger model — records fee charged on each LIVE fill."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class FeeLedger(Base):
    __tablename__ = "fee_ledger"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    order_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    fill_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, server_default="USDT")
    fee_amount: Mapped[Decimal] = mapped_column(Numeric(28, 8), nullable=False)
    fee_rate: Mapped[Decimal] = mapped_column(Numeric(10, 6), nullable=False)
    fill_value: Mapped[Decimal] = mapped_column(Numeric(28, 8), nullable=False, server_default="0")
    fill_quantity: Mapped[Decimal] = mapped_column(Numeric(28, 8), nullable=False, server_default="0")
    fill_price: Mapped[Decimal] = mapped_column(Numeric(28, 8), nullable=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
