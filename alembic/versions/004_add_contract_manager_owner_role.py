"""add contract manager owner role

Revision ID: 004_add_owner_role
Revises: 003_add_365_days
Create Date: 2026-01-14

"""

from alembic import op


# revision identifiers, used by Alembic.
# NOTE: alembic_version.version_num is VARCHAR(32) in this project, so keep revision ids <= 32 chars.
revision = "004_add_owner_role"
down_revision = "003_add_365_days"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add 'Contract Manager Owner' to the userrole enum (PostgreSQL).
    """
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'Contract Manager Owner';")


def downgrade() -> None:
    """
    Downgrade is a no-op for PostgreSQL enum value removals.
    """
    pass

