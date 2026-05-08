"""
ORM models for price_alerts and notification_preferences tables.
"""
import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class AlertCondition(str, enum.Enum):
    ABOVE = "ABOVE"
    BELOW = "BELOW"


class PriceAlert(Base):
    __tablename__ = "price_alerts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    condition: Mapped[AlertCondition] = mapped_column(
        SAEnum(AlertCondition, name="alert_condition", create_constraint=True),
        nullable=False,
    )
    target_price: Mapped[Decimal] = mapped_column(Numeric(28, 8), nullable=False)
    is_triggered: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    triggered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, unique=True
    )
    email_on_fill: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    email_on_margin_call: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    email_on_liquidation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    email_on_price_alert: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    user_email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
