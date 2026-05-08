"""Create options_contracts and options_positions tables

Revision ID: 005
Revises: 004
Create Date: 2026-05-08
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enums
    op.execute("CREATE TYPE option_type AS ENUM ('CALL', 'PUT')")
    op.execute(
        "CREATE TYPE options_position_status AS ENUM "
        "('OPEN', 'EXPIRED_ITM', 'EXPIRED_OTM')"
    )

    # ── options_contracts ──────────────────────────────────────────────────────
    op.create_table(
        "options_contracts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("underlying_symbol", sa.String(20), nullable=False),
        sa.Column(
            "option_type",
            sa.Enum("CALL", "PUT", name="option_type", create_type=False),
            nullable=False,
        ),
        sa.Column("strike_price", sa.Numeric(28, 8), nullable=False),
        sa.Column("expiry_date", sa.Date, nullable=False),
        sa.Column(
            "implied_volatility",
            sa.Numeric(10, 6),
            nullable=False,
            server_default="0.60",
        ),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_options_contracts_underlying_symbol",
        "options_contracts",
        ["underlying_symbol"],
    )

    # ── options_positions ──────────────────────────────────────────────────────
    op.create_table(
        "options_positions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("contract_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("underlying_symbol", sa.String(20), nullable=False),
        sa.Column(
            "option_type",
            sa.Enum("CALL", "PUT", name="option_type", create_type=False),
            nullable=False,
        ),
        sa.Column("strike_price", sa.Numeric(28, 8), nullable=False),
        sa.Column("expiry_date", sa.Date, nullable=False),
        sa.Column("quantity", sa.Numeric(28, 8), nullable=False),
        sa.Column("premium_paid", sa.Numeric(28, 8), nullable=False),
        sa.Column("settlement_price", sa.Numeric(28, 8), nullable=True),
        sa.Column("payout", sa.Numeric(28, 8), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "OPEN",
                "EXPIRED_ITM",
                "EXPIRED_OTM",
                name="options_position_status",
                create_type=False,
            ),
            nullable=False,
            server_default="OPEN",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
        sa.Column("settled_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_options_positions_user_id", "options_positions", ["user_id"])
    op.create_index(
        "ix_options_positions_contract_id", "options_positions", ["contract_id"]
    )


def downgrade() -> None:
    op.drop_table("options_positions")
    op.drop_table("options_contracts")
    op.execute("DROP TYPE IF EXISTS options_position_status")
    op.execute("DROP TYPE IF EXISTS option_type")
