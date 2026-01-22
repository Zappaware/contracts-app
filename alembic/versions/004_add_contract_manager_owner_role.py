"""add contract manager owner role

Revision ID: 004_add_owner_role
Revises: 003_add_365_days
Create Date: 2026-01-14

"""

from alembic import op
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
# NOTE: alembic_version.version_num is VARCHAR(32) in this project, so keep revision ids <= 32 chars.
revision = "004_add_owner_role"
down_revision = "003_add_365_days"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add 'Contract Manager Owner' to the userrole enum.
    
    For PostgreSQL: Uses ALTER TYPE to add the enum value.
    For SQL Server: No-op since enums are stored as strings and can accept any value.
    """
    bind = op.get_bind()
    inspector = inspect(bind)
    dialect_name = bind.dialect.name
    
    if dialect_name == 'postgresql':
        # PostgreSQL: Add value to enum type
        op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'Contract Manager Owner';")
    elif dialect_name == 'mssql':
        # SQL Server: Enums are stored as strings, so no action needed
        # The column can already accept the new value
        pass
    else:
        # For other databases, assume string-based enums (no action needed)
        pass


def downgrade() -> None:
    """
    Downgrade is a no-op for enum value removals.
    PostgreSQL does not support removing enum values directly.
    SQL Server doesn't need any action since enums are stored as strings.
    """
    pass

