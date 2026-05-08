"""Create user_position_limits, margin_calls, liquidations tables

Revision ID: 004
Revises: 003
Create Date: 2026-05-08

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── user_position_limits ───────────────────────────────────────────────────
    op.create_table(
        "user_position_limits",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column(
            "max_position_value_usdt",
            sa.Numeric(28, 8),
            nullable=False,
            server_default="50000",
            comment="Maximum total open position value in USDT",
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), onupdate=sa.text("now()")),
    )

    # ── margin_calls ──────────────────────────────────────────────────────────
    op.create_table(
        "margin_calls",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("margin_ratio_at_call", sa.Numeric(10, 4), nullable=False),
        sa.Column("price_at_call", sa.Numeric(28, 8), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_margin_calls_user_id", "margin_calls", ["user_id"])

    # ── liquidations ──────────────────────────────────────────────────────────
    op.create_table(
        "liquidations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("liquidation_price", sa.Numeric(28, 8), nullable=False),
        sa.Column("realised_pnl", sa.Numeric(28, 8), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
    )
    op.create_index("ix_liquidations_user_id", "liquidations", ["user_id"])


def downgrade() -> None:
    op.drop_table("liquidations")
    op.drop_table("margin_calls")
    op.drop_table("user_position_limits")
