"""
Portfolio holdings and P&L snapshot models.
These tables are owned by portfolio-service and managed via its Alembic migrations.
"""
import uuid
from datetime import date, datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class PortfolioHolding(Base):
    """
    One row per (user, asset, execution_mode).
    average_entry_price is recalculated on every BUY fill (weighted average).
    """
    __tablename__ = "portfolio_holdings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    asset: Mapped[str] = mapped_column(sa.String(20), nullable=False)
    quantity: Mapped[sa.Numeric] = mapped_column(
        sa.Numeric(28, 8), nullable=False, server_default="0"
    )
    average_entry_price: Mapped[sa.Numeric] = mapped_column(
        sa.Numeric(28, 8), nullable=False, server_default="0"
    )
    total_realised_pnl: Mapped[sa.Numeric] = mapped_column(
        sa.Numeric(28, 8), nullable=False, server_default="0"
    )
    execution_mode: Mapped[str] = mapped_column(
        sa.String(20), nullable=False, server_default="SIMULATION"
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.text("now()")
    )

    __table_args__ = (
        sa.UniqueConstraint(
            "user_id", "asset", "execution_mode",
            name="uq_portfolio_holding_user_asset_mode",
        ),
    )


class PnlSnapshot(Base):
    """
    Daily snapshot of a user's portfolio value and P&L totals.
    Written by the nightly scheduler task.
    """
    __tablename__ = "pnl_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    snapshot_date: Mapped[date] = mapped_column(sa.Date, nullable=False)
    total_realised_pnl: Mapped[sa.Numeric] = mapped_column(
        sa.Numeric(28, 8), nullable=False, server_default="0"
    )
    total_unrealised_pnl: Mapped[sa.Numeric] = mapped_column(
        sa.Numeric(28, 8), nullable=False, server_default="0"
    )
    total_portfolio_value: Mapped[sa.Numeric] = mapped_column(
        sa.Numeric(28, 8), nullable=False, server_default="0"
    )
    execution_mode: Mapped[str] = mapped_column(
        sa.String(20), nullable=False, server_default="SIMULATION"
    )

    __table_args__ = (
        sa.UniqueConstraint(
            "user_id", "snapshot_date", "execution_mode",
            name="uq_pnl_snapshot_user_date_mode",
        ),
    )
