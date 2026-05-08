"""Add fee_ledger table and sar_flags table

Revision ID: 003
Revises: 002
Create Date: 2025-07-01
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
    op.create_table(
        "fee_ledger",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("fill_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("currency", sa.String(10), nullable=False, server_default="USDT"),
        sa.Column("fee_amount", sa.Numeric(28, 8), nullable=False),
        sa.Column("fee_rate", sa.Numeric(10, 6), nullable=False),
        sa.Column("fill_value", sa.Numeric(28, 8), nullable=False, server_default="0"),
        sa.Column("fill_quantity", sa.Numeric(28, 8), nullable=False, server_default="0"),
        sa.Column("fill_price", sa.Numeric(28, 8), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_fee_ledger_user_id", "fee_ledger", ["user_id"])
    op.create_index("ix_fee_ledger_created_at", "fee_ledger", ["created_at"])

    # SAR flags table for compliance
    op.create_table(
        "sar_flags",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("flagged_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column("reference_tx_id", sa.String(100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_sar_flags_user_id", "sar_flags", ["user_id"])


def downgrade() -> None:
    op.drop_table("sar_flags")
    op.drop_table("fee_ledger")
