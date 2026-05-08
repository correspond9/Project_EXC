"""Read-only mirror of simulation_wallets (owned by wallet-service)."""
import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class SimulationWallet(Base):
    __tablename__ = "simulation_wallets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    currency: Mapped[str] = mapped_column(sa.String(10), nullable=False)
    balance: Mapped[sa.Numeric] = mapped_column(sa.Numeric(28, 8), nullable=False)
    locked_balance: Mapped[sa.Numeric] = mapped_column(sa.Numeric(28, 8), nullable=False)
    updated_at: Mapped[sa.DateTime] = mapped_column(sa.DateTime(timezone=True))
