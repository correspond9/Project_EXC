"""Risk service: tables created by order-service migration 004

Revision ID: 001
Revises:
Create Date: 2026-05-08

"""
from typing import Sequence, Union

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # margin_calls and liquidations tables are created by order-service migration 004.
    # Risk-service Alembic is kept here for version tracking only.
    pass


def downgrade() -> None:
    pass
