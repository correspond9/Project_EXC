"""Read/write mirror of user_position_limits table (created by order-service migration 004)."""
import uuid
from decimal import Decimal

from sqlalchemy import Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class UserPositionLimit(Base):
    __tablename__ = "user_position_limits"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, unique=True)
    max_position_value_usdt: Mapped[Decimal] = mapped_column(Numeric(28, 8), nullable=False)
    updated_at: Mapped[str | None] = mapped_column(nullable=True)
