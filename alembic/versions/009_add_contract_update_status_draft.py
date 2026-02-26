"""add draft to ContractUpdateStatus enum

Revision ID: 009_add_draft_status
Revises: 008_termination_docs
Create Date: 2026-02-18

"""
from alembic import op
from sqlalchemy import inspect


revision = "009_add_draft_status"
down_revision = "008_termination_docs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect_name = bind.dialect.name
    if dialect_name == "postgresql":
        op.execute("ALTER TYPE contractupdatestatus ADD VALUE IF NOT EXISTS 'draft'")
    # MSSQL and others: status column often stores string; no schema change needed


def downgrade() -> None:
    # PostgreSQL: removing enum value is complex and may break existing 'draft' rows; leave as no-op
    pass
