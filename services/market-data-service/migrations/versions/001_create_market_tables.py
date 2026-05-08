"""Create trading_pairs and price_history tables

Revision ID: 001
Revises:
Create Date: 2026-05-07

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── trading_pairs ─────────────────────────────────────────────────────────
    op.create_table(
        "trading_pairs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("binance_symbol", sa.String(20), nullable=False),
        sa.Column("base_asset", sa.String(10), nullable=False),
        sa.Column("quote_asset", sa.String(10), nullable=False),
        sa.Column(
            "market_type",
            sa.Enum("SPOT", "FUTURES", "OPTIONS", name="market_type"),
            nullable=False,
            server_default="SPOT",
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("min_quantity", sa.Numeric(30, 10), nullable=True),
        sa.Column("max_quantity", sa.Numeric(30, 10), nullable=True),
        sa.Column("price_tick_size", sa.Numeric(30, 10), nullable=True),
        sa.Column("quantity_step", sa.Numeric(30, 10), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_trading_pairs_symbol", "trading_pairs", ["symbol"], unique=True)
    op.create_index(
        "ix_trading_pairs_binance_symbol", "trading_pairs", ["binance_symbol"], unique=True
    )

    # ── price_history ─────────────────────────────────────────────────────────
    op.create_table(
        "price_history",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("interval", sa.String(5), nullable=False),
        sa.Column("open_time", sa.BigInteger(), nullable=False),
        sa.Column("open_price", sa.Numeric(30, 10), nullable=False),
        sa.Column("high_price", sa.Numeric(30, 10), nullable=False),
        sa.Column("low_price", sa.Numeric(30, 10), nullable=False),
        sa.Column("close_price", sa.Numeric(30, 10), nullable=False),
        sa.Column("volume", sa.Numeric(30, 10), nullable=False),
        sa.Column("close_time", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("symbol", "interval", "open_time", name="uq_price_history"),
    )
    op.create_index("ix_price_history_symbol", "price_history", ["symbol"])
    op.create_index(
        "ix_price_history_symbol_interval",
        "price_history",
        ["symbol", "interval", "open_time"],
    )


def downgrade() -> None:
    op.drop_table("price_history")
    op.drop_table("trading_pairs")
    op.execute(
        "DO $$ BEGIN "
        "DROP TYPE market_type; "
        "EXCEPTION WHEN undefined_object THEN NULL; "
        "END $$"
    )
