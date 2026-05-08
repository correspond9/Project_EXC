"""create portfolio_holdings and pnl_snapshots tables

Revision ID: 001
Revises:
Create Date: 2025-01-01 00:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")

    op.create_table(
        "portfolio_holdings",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset", sa.String(20), nullable=False),
        sa.Column("quantity", sa.Numeric(28, 8), nullable=False, server_default="0"),
        sa.Column("average_entry_price", sa.Numeric(28, 8), nullable=False, server_default="0"),
        sa.Column("total_realised_pnl", sa.Numeric(28, 8), nullable=False, server_default="0"),
        sa.Column("execution_mode", sa.String(20), nullable=False, server_default="SIMULATION"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint(
            "user_id", "asset", "execution_mode",
            name="uq_portfolio_holding_user_asset_mode",
        ),
    )
    op.create_index("ix_portfolio_holdings_user_id", "portfolio_holdings", ["user_id"])

    op.create_table(
        "pnl_snapshots",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("snapshot_date", sa.Date, nullable=False),
        sa.Column("total_realised_pnl", sa.Numeric(28, 8), nullable=False, server_default="0"),
        sa.Column("total_unrealised_pnl", sa.Numeric(28, 8), nullable=False, server_default="0"),
        sa.Column("total_portfolio_value", sa.Numeric(28, 8), nullable=False, server_default="0"),
        sa.Column("execution_mode", sa.String(20), nullable=False, server_default="SIMULATION"),
        sa.UniqueConstraint(
            "user_id", "snapshot_date", "execution_mode",
            name="uq_pnl_snapshot_user_date_mode",
        ),
    )
    op.create_index("ix_pnl_snapshots_user_id", "pnl_snapshots", ["user_id"])
    op.create_index("ix_pnl_snapshots_date", "pnl_snapshots", ["snapshot_date"])


def downgrade() -> None:
    op.drop_table("pnl_snapshots")
    op.drop_table("portfolio_holdings")
