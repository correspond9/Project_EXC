import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class SimulationWallet(Base):
    """
    One row per (user, currency) combination.
    Each user starts with a single USDT wallet; more currencies can be added
    as the platform grows (e.g. after a trade fills in ETH).
    """

    __tablename__ = "simulation_wallets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USDT")

    # Available balance — can be used to place new orders
    balance: Mapped[Decimal] = mapped_column(
        Numeric(28, 8), nullable=False, server_default="0"
    )
    # Locked balance — reserved for open orders; released on cancel/fill
    locked_balance: Mapped[Decimal] = mapped_column(
        Numeric(28, 8), nullable=False, server_default="0"
    )

    updated_at: Mapped[str] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )
