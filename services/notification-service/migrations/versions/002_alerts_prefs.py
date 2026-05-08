"""Create price_alerts and notification_preferences tables

Revision ID: 002
Revises: 001
Create Date: 2026-05-08
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
    # ── price_alerts ──────────────────────────────────────────────────────────
    op.create_table(
        "price_alerts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column(
            "condition",
            sa.Enum("ABOVE", "BELOW", name="alert_condition"),
            nullable=False,
        ),
        sa.Column("target_price", sa.Numeric(28, 8), nullable=False),
        sa.Column("is_triggered", sa.Boolean, nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
        sa.Column("triggered_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_price_alerts_user_id", "price_alerts", ["user_id"])
    op.create_index(
        "ix_price_alerts_symbol_active",
        "price_alerts",
        ["symbol", "is_triggered"],
    )

    # ── notification_preferences ──────────────────────────────────────────────
    op.create_table(
        "notification_preferences",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            unique=True,
        ),
        sa.Column("email_on_fill", sa.Boolean, nullable=False, server_default="true"),
        sa.Column(
            "email_on_margin_call", sa.Boolean, nullable=False, server_default="true"
        ),
        sa.Column(
            "email_on_liquidation", sa.Boolean, nullable=False, server_default="true"
        ),
        sa.Column(
            "email_on_price_alert", sa.Boolean, nullable=False, server_default="true"
        ),
        sa.Column(
            "user_email",
            sa.String(254),
            nullable=True,
            comment="Cached email address for outbound mail",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
    )


def downgrade() -> None:
    op.drop_table("notification_preferences")
    op.drop_table("price_alerts")
    op.execute("DROP TYPE IF EXISTS alert_condition")
