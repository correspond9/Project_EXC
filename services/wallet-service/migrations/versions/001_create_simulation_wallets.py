"""Create simulation_wallets table

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
    op.create_table(
        "simulation_wallets",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        # user_id references users table in the same DB (created by user-service migration)
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("currency", sa.String(10), nullable=False, server_default="USDT"),
        sa.Column("balance", sa.Numeric(28, 8), nullable=False, server_default="0"),
        sa.Column("locked_balance", sa.Numeric(28, 8), nullable=False, server_default="0"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        # One row per (user, currency)
        sa.UniqueConstraint("user_id", "currency", name="uq_simulation_wallet_user_currency"),
    )
    op.create_index("ix_simulation_wallets_user_id", "simulation_wallets", ["user_id"])


def downgrade() -> None:
    op.drop_table("simulation_wallets")
