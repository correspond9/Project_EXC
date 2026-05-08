"""
Admin-service — market configuration and fee configuration models.
These tables are owned by admin-service.
"""
import uuid
from decimal import Decimal

from sqlalchemy import Boolean, Numeric, String, Integer, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class TradingPairConfig(Base):
    """
    Controls which trading pairs are available and with what leverage limits.
    Seeded at migration time; admin can enable/disable and adjust limits.
    """
    __tablename__ = "trading_pair_configs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    max_leverage: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    updated_at: Mapped[str] = mapped_column(server_default=text("now()"), onupdate=text("now()"))


class FeeConfig(Base):
    """
    Platform-wide and per-user fee overrides.
    If user_id is NULL it represents the global default.
    """
    __tablename__ = "fee_configs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, unique=True)
    maker_fee: Mapped[Decimal] = mapped_column(Numeric(8, 6), default=Decimal("0.001"))
    taker_fee: Mapped[Decimal] = mapped_column(Numeric(8, 6), default=Decimal("0.001"))
    updated_at: Mapped[str] = mapped_column(server_default=text("now()"), onupdate=text("now()"))
