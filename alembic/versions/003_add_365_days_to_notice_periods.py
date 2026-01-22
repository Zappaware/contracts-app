"""add 365 days to notice period enums

Revision ID: 003_add_365_days
Revises: 002
Create Date: 2025-11-05 04:20:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '003_add_365_days'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add '365 days (1 year)' option to notice period enums
    
    This migration adds the new enum value to:
    - termination_notice_period (noticeperiodtype)
    - expiration_notice_frequency (expirationnoticeperiodtype)
    
    For PostgreSQL: Uses ALTER TYPE to add the enum values.
    For SQL Server: No-op since enums are stored as strings and can accept any value.
    """
    bind = op.get_bind()
    inspector = inspect(bind)
    dialect_name = bind.dialect.name
    
    if dialect_name == 'postgresql':
        # PostgreSQL: Add value to enum types
        # Note: This requires PostgreSQL 9.1+
        
        # Add to termination_notice_period enum
        op.execute("""
            ALTER TYPE noticeperiodtype ADD VALUE IF NOT EXISTS '365 days (1 year)';
        """)
        
        # Add to expiration_notice_frequency enum  
        op.execute("""
            ALTER TYPE expirationnoticeperiodtype ADD VALUE IF NOT EXISTS '365 days (1 year)';
        """)
    elif dialect_name == 'mssql':
        # SQL Server: Enums are stored as strings, so no action needed
        # The columns can already accept the new value
        pass
    else:
        # For other databases, assume string-based enums (no action needed)
        pass


def downgrade():
    """
    Note: PostgreSQL does not support removing enum values directly.
    To downgrade, you would need to:
    1. Create new enum types without the value
    2. Alter columns to use the new types
    3. Drop the old types
    
    This is complex and risky, so we're leaving this as a no-op.
    SQL Server doesn't need any action since enums are stored as strings.
    """
    pass