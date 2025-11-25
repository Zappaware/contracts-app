"""add 365 days to notice period enums

Revision ID: 003_add_365_days
Revises: 002_fix_contract_enum_types
Create Date: 2025-11-05 04:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003_add_365_days'
down_revision = '002_fix_contract_enum_types'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add '365 days (1 year)' option to notice period enums
    
    This migration adds the new enum value to:
    - termination_notice_period (NoticePeriodType)
    - expiration_notice_frequency (ExpirationNoticePeriodType)
    """
    
    # For PostgreSQL, we need to use ALTER TYPE to add new enum values
    # Note: This requires PostgreSQL 9.1+
    
    # Add to termination_notice_period enum
    op.execute("""
        ALTER TYPE "NoticePeriodType" ADD VALUE IF NOT EXISTS '365 days (1 year)';
    """)
    
    # Add to expiration_notice_frequency enum  
    op.execute("""
        ALTER TYPE "ExpirationNoticePeriodType" ADD VALUE IF NOT EXISTS '365 days (1 year)';
    """)


def downgrade():
    """
    Note: PostgreSQL does not support removing enum values directly.
    To downgrade, you would need to:
    1. Create new enum types without the value
    2. Alter columns to use the new types
    3. Drop the old types
    
    This is complex and risky, so we're leaving this as a no-op.
    If you need to downgrade, consider creating a new migration.
    """
    pass