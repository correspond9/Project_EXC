"""Add KYC notification types to notification_type enum

Revision ID: 003
Revises: 002
Create Date: 2026-05-08

"""
from typing import Sequence, Union

from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ALTER TYPE cannot run inside a transaction block in PostgreSQL — use COMMIT trick via execute
    op.execute("ALTER TYPE notification_type ADD VALUE IF NOT EXISTS 'KYC_SUBMITTED'")
    op.execute("ALTER TYPE notification_type ADD VALUE IF NOT EXISTS 'KYC_APPROVED'")
    op.execute("ALTER TYPE notification_type ADD VALUE IF NOT EXISTS 'KYC_REJECTED'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values — no-op downgrade
    pass
