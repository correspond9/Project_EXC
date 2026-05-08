"""Read-only mirror of the margin_accounts table (created by order-service)."""
import enum
import uuid
from decimal import Decimal

from sqlalchemy import Enum as SAEnum, Numeric, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class FuturesExecutionMode(str, enum.Enum):
    SIMULATION = "SIMULATION"
    LIVE = "LIVE"


class MarginAccount(Base):
    __tablename__ = "margin_accounts"
    __table_args__ = (
        UniqueConstraint("user_id", "execution_mode", name="uq_margin_user_mode"),
        {"extend_existing": True},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    execution_mode: Mapped[FuturesExecutionMode] = mapped_column(
        SAEnum(FuturesExecutionMode, name="execution_mode", create_constraint=False),
        nullable=False,
        server_default="SIMULATION",
    )
    total_margin_balance: Mapped[Decimal] = mapped_column(
        Numeric(28, 8), nullable=False, server_default="0"
    )
    available_margin: Mapped[Decimal] = mapped_column(
        Numeric(28, 8), nullable=False, server_default="0"
    )
    used_margin: Mapped[Decimal] = mapped_column(
        Numeric(28, 8), nullable=False, server_default="0"
    )
    updated_at: Mapped[str] = mapped_column(server_default=func.now(), onupdate=func.now())
