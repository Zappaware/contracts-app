"""fix_contract_enum_types

Revision ID: 002
Revises: 001
Create Date: 2025-10-06 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Fix contract enum types that were incorrectly set to userrole type.
    
    For PostgreSQL: Changes enum types using ALTER TABLE ... ALTER COLUMN ... TYPE.
    For SQL Server: No-op since enums are stored as strings and don't have type constraints.
    """
    bind = op.get_bind()
    inspector = inspect(bind)
    dialect_name = bind.dialect.name
    
    if dialect_name == 'postgresql':
        # Fix contract_type column
        op.execute("ALTER TABLE contracts ALTER COLUMN contract_type TYPE contracttype USING contract_type::text::contracttype")
        
        # Fix automatic_renewal column
        op.execute("ALTER TABLE contracts ALTER COLUMN automatic_renewal TYPE automaticrenewaltype USING automatic_renewal::text::automaticrenewaltype")
        
        # Fix renewal_period column
        op.execute("ALTER TABLE contracts ALTER COLUMN renewal_period TYPE renewalperiodtype USING renewal_period::text::renewalperiodtype")
        
        # Fix department column
        op.execute("ALTER TABLE contracts ALTER COLUMN department TYPE departmenttype USING department::text::departmenttype")
        
        # Fix contract_currency column
        op.execute("ALTER TABLE contracts ALTER COLUMN contract_currency TYPE currencytype USING contract_currency::text::currencytype")
        
        # Fix payment_method column
        op.execute("ALTER TABLE contracts ALTER COLUMN payment_method TYPE paymentmethodtype USING payment_method::text::paymentmethodtype")
        
        # Fix termination_notice_period column
        op.execute("ALTER TABLE contracts ALTER COLUMN termination_notice_period TYPE noticeperiodtype USING termination_notice_period::text::noticeperiodtype")
        
        # Fix expiration_notice_frequency column
        op.execute("ALTER TABLE contracts ALTER COLUMN expiration_notice_frequency TYPE expirationnoticeperiodtype USING expiration_notice_frequency::text::expirationnoticeperiodtype")
        
        # Fix status column
        op.execute("ALTER TABLE contracts ALTER COLUMN status TYPE contractstatustype USING status::text::contractstatustype")
        
        # Fix contract_termination column
        op.execute("ALTER TABLE contracts ALTER COLUMN contract_termination TYPE contractterminationtype USING contract_termination::text::contractterminationtype")
    elif dialect_name == 'mssql':
        # SQL Server: Enums are stored as strings, so no action needed
        # The columns are already string-based and don't have enum type constraints
        pass
    else:
        # For other databases, assume string-based enums (no action needed)
        pass


def downgrade() -> None:
    """
    Revert all columns back to userrole type (PostgreSQL only).
    For SQL Server, this is a no-op since enums are stored as strings.
    """
    bind = op.get_bind()
    inspector = inspect(bind)
    dialect_name = bind.dialect.name
    
    if dialect_name == 'postgresql':
        # Revert all columns back to userrole type
        op.execute("ALTER TABLE contracts ALTER COLUMN contract_type TYPE userrole USING contract_type::text::userrole")
        op.execute("ALTER TABLE contracts ALTER COLUMN automatic_renewal TYPE userrole USING automatic_renewal::text::userrole")
        op.execute("ALTER TABLE contracts ALTER COLUMN renewal_period TYPE userrole USING renewal_period::text::userrole")
        op.execute("ALTER TABLE contracts ALTER COLUMN department TYPE userrole USING department::text::userrole")
        op.execute("ALTER TABLE contracts ALTER COLUMN contract_currency TYPE userrole USING contract_currency::text::userrole")
        op.execute("ALTER TABLE contracts ALTER COLUMN payment_method TYPE userrole USING payment_method::text::userrole")
        op.execute("ALTER TABLE contracts ALTER COLUMN termination_notice_period TYPE userrole USING termination_notice_period::text::userrole")
        op.execute("ALTER TABLE contracts ALTER COLUMN expiration_notice_frequency TYPE userrole USING expiration_notice_frequency::text::userrole")
        op.execute("ALTER TABLE contracts ALTER COLUMN status TYPE userrole USING status::text::userrole")
        op.execute("ALTER TABLE contracts ALTER COLUMN contract_termination TYPE userrole USING contract_termination::text::userrole")
    elif dialect_name == 'mssql':
        # SQL Server: No-op
        pass
    else:
        # For other databases, assume no-op
        pass