"""Add real wallet tables: real_wallets, balance_ledger, deposit_addresses, withdrawal_requests

Revision ID: 002
Revises: 001
Create Date: 2025-07-01
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enums
    op.execute(
        "CREATE TYPE ledger_tx_type AS ENUM "
        "('DEPOSIT','WITHDRAWAL','TRADE_FEE','TRADE_FILL','ADMIN_CREDIT')"
    )
    op.execute(
        "CREATE TYPE withdrawal_status AS ENUM "
        "('PENDING','APPROVED','REJECTED','COMPLETED')"
    )

    op.create_table(
        "real_wallets",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("currency", sa.String(10), nullable=False, server_default="USDT"),
        sa.Column("balance", sa.Numeric(28, 8), nullable=False, server_default="0"),
        sa.Column("locked_balance", sa.Numeric(28, 8), nullable=False, server_default="0"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            onupdate=sa.text("now()"),
        ),
        sa.UniqueConstraint("user_id", "currency", name="uq_real_wallet_user_currency"),
    )
    op.create_index("ix_real_wallets_user_id", "real_wallets", ["user_id"])

    op.create_table(
        "balance_ledger",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("currency", sa.String(10), nullable=False),
        sa.Column("amount", sa.Numeric(28, 8), nullable=False),
        sa.Column("balance_after", sa.Numeric(28, 8), nullable=False),
        sa.Column(
            "tx_type",
            postgresql.ENUM(
                "DEPOSIT", "WITHDRAWAL", "TRADE_FEE", "TRADE_FILL", "ADMIN_CREDIT",
                name="ledger_tx_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("reference_id", sa.String(100), nullable=True),
        sa.Column("note", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_balance_ledger_user_id", "balance_ledger", ["user_id"])
    op.create_index("ix_balance_ledger_created_at", "balance_ledger", ["created_at"])

    op.create_table(
        "deposit_addresses",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("currency", sa.String(10), nullable=False),
        sa.Column("network", sa.String(20), nullable=False),
        sa.Column("address", sa.String(200), nullable=False),
        sa.Column("assigned_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("user_id", "currency", "network", name="uq_deposit_address"),
    )

    op.create_table(
        "withdrawal_requests",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("currency", sa.String(10), nullable=False),
        sa.Column("amount", sa.Numeric(28, 8), nullable=False),
        sa.Column("destination_address", sa.String(200), nullable=False),
        sa.Column("network", sa.String(20), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "PENDING", "APPROVED", "REJECTED", "COMPLETED",
                name="withdrawal_status",
                create_type=False,
            ),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column("admin_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("rejection_reason", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            onupdate=sa.text("now()"),
        ),
    )
    op.create_index("ix_withdrawal_requests_user_id", "withdrawal_requests", ["user_id"])
    op.create_index("ix_withdrawal_requests_status", "withdrawal_requests", ["status"])


def downgrade() -> None:
    op.drop_table("withdrawal_requests")
    op.drop_table("deposit_addresses")
    op.drop_table("balance_ledger")
    op.drop_table("real_wallets")
    op.execute("DROP TYPE IF EXISTS withdrawal_status")
    op.execute("DROP TYPE IF EXISTS ledger_tx_type")
