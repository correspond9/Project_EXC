"""
SQLAlchemy model for the simulation_wallets table owned by wallet-service.
The simulation engine reads and writes this table directly (same shared DB).
"""
import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class SimulationWallet(Base):
    __tablename__ = "simulation_wallets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    currency: Mapped[str] = mapped_column(sa.String(10), nullable=False, default="USDT")
    balance: Mapped[sa.Numeric] = mapped_column(
        sa.Numeric(28, 8), nullable=False, server_default="0"
    )
    locked_balance: Mapped[sa.Numeric] = mapped_column(
        sa.Numeric(28, 8), nullable=False, server_default="0"
    )
    updated_at: Mapped[sa.DateTime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.text("now()")
    )
