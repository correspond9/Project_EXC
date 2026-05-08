"""
Sprint 21 — Platform controls: per-user leverage cap and live_trading_enabled flag.

Revision ID: 004
Revises: 003
Create Date: 2026-06-01

Changes
-------
- users.max_leverage_override  INTEGER NULL
    NULL  = use platform default (no per-user cap)
    N     = hard ceiling for this user's FUTURES leverage
- users.live_trading_enabled   BOOLEAN NOT NULL DEFAULT TRUE
    FALSE = this user is blocked from LIVE mode even with KYC approval
    (used during beta rollout to gate individual users)
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Per-user leverage ceiling (NULL = use platform default)
    op.add_column(
        "users",
        sa.Column("max_leverage_override", sa.Integer(), nullable=True),
    )

    # Beta gate: operator can individually allow/block LIVE mode
    op.add_column(
        "users",
        sa.Column(
            "live_trading_enabled",
            sa.Boolean(),
            nullable=False,
            server_default="true",
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "live_trading_enabled")
    op.drop_column("users", "max_leverage_override")
