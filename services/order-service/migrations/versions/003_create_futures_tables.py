"""Create positions and margin_accounts tables; add leverage/reduce_only to orders

Revision ID: 003
Revises: 002
Create Date: 2026-05-08

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── New ENUMs ──────────────────────────────────────────────────────────────
    for name, values in [
        ("position_side", ("LONG", "SHORT")),
        ("position_status", ("OPEN", "CLOSED", "LIQUIDATED")),
    ]:
        vals = ", ".join(f"'{v}'" for v in values)
        op.execute(
            f"DO $$ BEGIN CREATE TYPE {name} AS ENUM ({vals}); "
            f"EXCEPTION WHEN duplicate_object THEN NULL; END $$"
        )

    # ── Add columns to orders ─────────────────────────────────────────────────
    op.add_column("orders", sa.Column("leverage", sa.Integer(), nullable=True))
    op.add_column("orders", sa.Column("reduce_only", sa.Boolean(), nullable=False, server_default="false"))

    # ── margin_accounts ───────────────────────────────────────────────────────
    op.create_table(
        "margin_accounts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "execution_mode",
            sa.Enum("SIMULATION", "LIVE", name="execution_mode", create_type=False),
            nullable=False,
            server_default="SIMULATION",
        ),
        sa.Column("total_margin_balance", sa.Numeric(28, 8), nullable=False, server_default="0"),
        sa.Column("available_margin", sa.Numeric(28, 8), nullable=False, server_default="0"),
        sa.Column("used_margin", sa.Numeric(28, 8), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("user_id", "execution_mode", name="uq_margin_user_mode"),
    )
    op.create_index("ix_margin_accounts_user_id", "margin_accounts", ["user_id"])

    # ── positions ─────────────────────────────────────────────────────────────
    op.create_table(
        "positions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column(
            "side",
            sa.Enum("LONG", "SHORT", name="position_side", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "execution_mode",
            sa.Enum("SIMULATION", "LIVE", name="execution_mode", create_type=False),
            nullable=False,
            server_default="SIMULATION",
        ),
        sa.Column("quantity", sa.Numeric(28, 8), nullable=False),
        sa.Column("entry_price", sa.Numeric(28, 8), nullable=False),
        sa.Column("leverage", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("margin", sa.Numeric(28, 8), nullable=False),
        sa.Column("liquidation_price", sa.Numeric(28, 8), nullable=False),
        sa.Column("unrealised_pnl", sa.Numeric(28, 8), nullable=False, server_default="0"),
        sa.Column("realised_pnl", sa.Numeric(28, 8), nullable=True),
        sa.Column("closed_price", sa.Numeric(28, 8), nullable=True),
        sa.Column(
            "status",
            sa.Enum("OPEN", "CLOSED", "LIQUIDATED", name="position_status", create_type=False),
            nullable=False,
            server_default="OPEN",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_positions_user_id", "positions", ["user_id"])
    op.create_index("ix_positions_status", "positions", ["status"])
    op.create_index("ix_positions_symbol", "positions", ["symbol"])


def downgrade() -> None:
    op.drop_table("positions")
    op.drop_table("margin_accounts")
    op.drop_column("orders", "reduce_only")
    op.drop_column("orders", "leverage")
    op.execute("DROP TYPE IF EXISTS position_status")
    op.execute("DROP TYPE IF EXISTS position_side")
