"""Create kyc_documents table

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
    # ENUM types (kyc_document_type, kyc_document_status) are created
    # automatically by SQLAlchemy via _on_table_create.
    op.create_table(
        "kyc_documents",
        sa.Column(
            "id",
            sa.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            sa.UUID(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "document_type",
            sa.Enum(
                "PASSPORT",
                "EMIRATES_ID",
                "SELFIE",
                "PROOF_OF_ADDRESS",
                name="kyc_document_type",
            ),
            nullable=False,
        ),
        sa.Column("file_reference", sa.String(500), nullable=False),
        sa.Column(
            "verification_status",
            sa.Enum(
                "PENDING",
                "VERIFIED",
                "REJECTED",
                name="kyc_document_status",
            ),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_kyc_documents_user_id", "kyc_documents", ["user_id"])

    op.execute(
        """
        CREATE TRIGGER kyc_documents_updated_at
        BEFORE UPDATE ON kyc_documents
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS kyc_documents_updated_at ON kyc_documents")
    op.drop_index("ix_kyc_documents_user_id", table_name="kyc_documents")
    op.drop_table("kyc_documents")

    op.execute("DROP TYPE IF EXISTS kyc_document_status")
    op.execute("DROP TYPE IF EXISTS kyc_document_type")
