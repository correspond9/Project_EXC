"""Add PARTNER, POWER_USER, SUPER_USER roles; referred_by column;
partner_permissions and commission_ledger tables.

Revision ID: 003
Revises: 002
Create Date: 2026-05-08

Notes
-----
PostgreSQL 12+ allows ALTER TYPE ... ADD VALUE inside a transaction but the
new value cannot be used in the *same* transaction.  Because we only CREATE
new tables and ADD a nullable column after adding the enum values (we do NOT
insert rows with the new values), this migration is safe to run inside a
single transaction on PostgreSQL 16.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. Extend user_role enum with three new values ────────────────────────
    # IF NOT EXISTS prevents re-run failures during development resets.
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'PARTNER'")
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'POWER_USER'")
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'SUPER_USER'")

    # ── 2. Add referred_by column to users ────────────────────────────────────
    op.add_column(
        "users",
        sa.Column(
            "referred_by",
            sa.UUID(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_users_referred_by", "users", ["referred_by"])

    # ── 3. partner_permissions ────────────────────────────────────────────────
    op.create_table(
        "partner_permissions",
        sa.Column(
            "id",
            sa.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "partner_user_id",
            sa.UUID(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("permission", sa.String(100), nullable=False),
        sa.Column(
            "granted_by",
            sa.UUID(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "granted_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_partner_permissions_partner_user_id",
        "partner_permissions",
        ["partner_user_id"],
    )
    # Unique: a partner can hold each permission at most once
    op.create_index(
        "uq_partner_permissions_partner_permission",
        "partner_permissions",
        ["partner_user_id", "permission"],
        unique=True,
    )

    # ── 4. commission_ledger ──────────────────────────────────────────────────
    op.create_table(
        "commission_ledger",
        sa.Column(
            "id",
            sa.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "partner_user_id",
            sa.UUID(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "referred_user_id",
            sa.UUID(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("trade_reference", sa.String(255), nullable=True),
        sa.Column("commission_amount", sa.Numeric(28, 8), nullable=False),
        sa.Column("commission_rate", sa.Numeric(10, 6), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_commission_ledger_partner_user_id",
        "commission_ledger",
        ["partner_user_id"],
    )
    op.create_index(
        "ix_commission_ledger_referred_user_id",
        "commission_ledger",
        ["referred_user_id"],
    )
    op.create_index(
        "ix_commission_ledger_created_at",
        "commission_ledger",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_table("commission_ledger")
    op.drop_table("partner_permissions")

    op.drop_index("ix_users_referred_by", table_name="users")
    op.drop_column("users", "referred_by")

    # PostgreSQL does not support DROP VALUE on enum types.
    # To fully roll back the enum changes, recreate the type without the new values.
    # This is a destructive operation and should only be done in development.
    op.execute("""
        ALTER TYPE user_role RENAME TO user_role_old;
        CREATE TYPE user_role AS ENUM ('STUDENT', 'TRADER', 'ADMIN', 'SUPER_ADMIN');
        ALTER TABLE users
            ALTER COLUMN role TYPE user_role
            USING role::text::user_role;
        DROP TYPE user_role_old;
    """)
