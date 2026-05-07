"""Create orders and order_fills tables

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
    # ── ENUMs ─────────────────────────────────────────────────────────────────
    for name, values in [
        ("order_side", ("BUY", "SELL")),
        ("order_type", ("MARKET", "LIMIT", "STOP_LOSS", "TAKE_PROFIT")),
        ("market_type_order", ("SPOT", "FUTURES", "OPTIONS")),
        ("order_status", ("PENDING", "OPEN", "PARTIALLY_FILLED", "FILLED", "CANCELLED", "REJECTED")),
        ("execution_mode", ("SIMULATION", "LIVE")),
    ]:
        vals = ", ".join(f"'{v}'" for v in values)
        op.execute(
            f"DO $$ BEGIN CREATE TYPE {name} AS ENUM ({vals}); "
            f"EXCEPTION WHEN duplicate_object THEN NULL; END $$"
        )

    # ── orders ────────────────────────────────────────────────────────────────
    op.create_table(
        "orders",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column(
            "side",
            sa.Enum("BUY", "SELL", name="order_side", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "order_type",
            sa.Enum("MARKET", "LIMIT", "STOP_LOSS", "TAKE_PROFIT", name="order_type", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "market_type",
            sa.Enum("SPOT", "FUTURES", "OPTIONS", name="market_type_order", create_type=False),
            nullable=False,
            server_default="SPOT",
        ),
        sa.Column("quantity", sa.Numeric(28, 8), nullable=False),
        sa.Column("price", sa.Numeric(28, 8), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "PENDING", "OPEN", "PARTIALLY_FILLED", "FILLED", "CANCELLED", "REJECTED",
                name="order_status",
                create_type=False,
            ),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column(
            "execution_mode",
            sa.Enum("SIMULATION", "LIVE", name="execution_mode", create_type=False),
            nullable=False,
            server_default="SIMULATION",
        ),
        sa.Column("external_order_id", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_orders_user_id", "orders", ["user_id"])
    op.create_index("ix_orders_symbol", "orders", ["symbol"])
    op.create_index("ix_orders_status", "orders", ["status"])

    # ── order_fills ───────────────────────────────────────────────────────────
    op.create_table(
        "order_fills",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "order_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("orders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("fill_price", sa.Numeric(28, 8), nullable=False),
        sa.Column("fill_quantity", sa.Numeric(28, 8), nullable=False),
        sa.Column("fee", sa.Numeric(28, 8), nullable=False, server_default="0"),
        sa.Column("fee_currency", sa.String(10), nullable=False, server_default="USDT"),
        sa.Column(
            "execution_mode",
            sa.Enum("SIMULATION", "LIVE", name="execution_mode", create_type=False),
            nullable=False,
        ),
        sa.Column("filled_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_order_fills_order_id", "order_fills", ["order_id"])


def downgrade() -> None:
    op.drop_table("order_fills")
    op.drop_table("orders")
    for name in ["execution_mode", "order_status", "market_type_order", "order_type", "order_side"]:
        op.execute(
            f"DO $$ BEGIN DROP TYPE {name}; EXCEPTION WHEN undefined_object THEN NULL; END $$"
        )
