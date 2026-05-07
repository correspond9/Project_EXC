"""Add stop_price column to orders table

Revision ID: 002
Revises: 001
Create Date: 2026-05-08

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "orders",
        sa.Column("stop_price", sa.Numeric(28, 8), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("orders", "stop_price")
