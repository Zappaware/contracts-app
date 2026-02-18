"""add termination_documents table

Revision ID: 008_termination_docs
Revises: 006_add_update_decision_fields
Create Date: 2026-02-18

"""
from alembic import op
import sqlalchemy as sa


revision = "008_termination_docs"
down_revision = "006_add_update_decision_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "termination_documents",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("contract_id", sa.Integer(), sa.ForeignKey("contracts.id"), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("document_name", sa.String(255), nullable=False),
        sa.Column("document_date", sa.Date(), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("termination_documents")
