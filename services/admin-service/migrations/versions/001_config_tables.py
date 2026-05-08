"""Admin-service config tables: trading_pair_configs, fee_configs

Revision ID: 001
Revises: None
Create Date: 2025-01-01 00:00:00.000000

"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SEED_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
    "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "DOTUSDT", "MATICUSDT",
]


def upgrade() -> None:
    # Trading pair configuration table
    op.create_table(
        "trading_pair_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("symbol", sa.String(20), nullable=False, unique=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("max_leverage", sa.Integer, nullable=False, server_default="10"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_trading_pair_configs_symbol", "trading_pair_configs", ["symbol"])

    # Seed default pairs
    op.execute(
        sa.text(
            "INSERT INTO trading_pair_configs (id, symbol, is_active, max_leverage) "
            "VALUES " + ", ".join(
                f"(gen_random_uuid(), '{sym}', true, 125)" for sym in SEED_SYMBOLS
            )
        )
    )

    # Fee configuration table (NULL user_id = platform default)
    op.create_table(
        "fee_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True, unique=True),
        sa.Column("maker_fee", sa.Numeric(8, 6), nullable=False, server_default="0.001"),
        sa.Column("taker_fee", sa.Numeric(8, 6), nullable=False, server_default="0.001"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_fee_configs_user_id", "fee_configs", ["user_id"])

    # Insert platform default fee row
    op.execute(
        sa.text(
            "INSERT INTO fee_configs (id, user_id, maker_fee, taker_fee) "
            "VALUES (gen_random_uuid(), NULL, 0.001, 0.001)"
        )
    )


def downgrade() -> None:
    op.drop_table("fee_configs")
    op.drop_table("trading_pair_configs")
