"""initial_schema

Revision ID: 001
Revises: 
Create Date: 2025-10-06 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def _get_enum_type(*values, name=None, create_type=True):
    """
    Helper function to get the appropriate enum type based on database dialect.
    For PostgreSQL: Returns postgresql.ENUM with create_type parameter
    For SQL Server: Returns sa.Enum (which creates string columns)
    """
    bind = op.get_bind()
    dialect_name = bind.dialect.name
    
    if dialect_name == 'postgresql':
        return postgresql.ENUM(*values, name=name, create_type=create_type)
    else:
        # For SQL Server and other databases, use sa.Enum which creates string columns
        return sa.Enum(*values, name=name)


def upgrade() -> None:
    bind = op.get_bind()
    dialect_name = bind.dialect.name
    
    # Create all enum types first (PostgreSQL only)
    if dialect_name == 'postgresql':
        # Vendor enums
        materialoutsourcingtype = postgresql.ENUM('Yes', 'No', name='materialoutsourcingtype')
        materialoutsourcingtype.create(op.get_bind(), checkfirst=True)
        
        bankcustomertype = postgresql.ENUM('Aruba Bank', 'Orco Bank', 'None', name='bankcustomertype')
        bankcustomertype.create(op.get_bind(), checkfirst=True)
        
        duediligencerequiredtype = postgresql.ENUM('Yes', 'No', name='duediligencerequiredtype')
        duediligencerequiredtype.create(op.get_bind(), checkfirst=True)
        
        alertfrequencytype = postgresql.ENUM('15 days', '30 days', '60 days', '90 days', '120 days', name='alertfrequencytype')
        alertfrequencytype.create(op.get_bind(), checkfirst=True)
        
        vendorstatustype = postgresql.ENUM('Active', 'Inactive', name='vendorstatustype')
        vendorstatustype.create(op.get_bind(), checkfirst=True)
        
        documenttype = postgresql.ENUM(
            'Due Diligence',
            'Non-Disclosure Agreement',
            'Integrity Policy',
            'Risk Assessment Form',
            'Business Continuity Plan',
            'Disaster Recovery Plan',
            'Insurance Policy',
            name='documenttype'
        )
        documenttype.create(op.get_bind(), checkfirst=True)
        
        # Contract enums
        contracttype = postgresql.ENUM(
            'Service Agreement',
            'Maintenance Contract',
            'Software License',
            'Consulting Agreement',
            'Support Contract',
            'Lease Agreement',
            'Purchase Agreement',
            'Non-Disclosure Agreement',
            'Partnership Agreement',
            'Outsourcing Agreement',
            name='contracttype'
        )
        contracttype.create(op.get_bind(), checkfirst=True)
        
        automaticrenewaltype = postgresql.ENUM('Yes', 'No', name='automaticrenewaltype')
        automaticrenewaltype.create(op.get_bind(), checkfirst=True)
        
        renewalperiodtype = postgresql.ENUM('1 Year', '2 Years', '3 Years', name='renewalperiodtype')
        renewalperiodtype.create(op.get_bind(), checkfirst=True)
        
        departmenttype = postgresql.ENUM(
            'Human Resources',
            'Finance',
            'IT',
            'Operations',
            'Legal',
            'Marketing',
            'Sales',
            'Customer Service',
            'Risk Management',
            'Compliance',
            'Audit',
            'Treasury',
            'Credit',
            'Retail Banking',
            'Corporate Banking',
            name='departmenttype'
        )
        departmenttype.create(op.get_bind(), checkfirst=True)
        
        noticeperiodtype = postgresql.ENUM('15 days', '30 days', '60 days', '90 days', '120 days', name='noticeperiodtype')
        noticeperiodtype.create(op.get_bind(), checkfirst=True)
        
        expirationnoticeperiodtype = postgresql.ENUM('15 days', '30 days', '60 days', '90 days', '120 days', name='expirationnoticeperiodtype')
        expirationnoticeperiodtype.create(op.get_bind(), checkfirst=True)
        
        currencytype = postgresql.ENUM('AWG', 'XCG', 'USD', 'EUR', name='currencytype')
        currencytype.create(op.get_bind(), checkfirst=True)
        
        paymentmethodtype = postgresql.ENUM('Invoice', 'Standing Order', name='paymentmethodtype')
        paymentmethodtype.create(op.get_bind(), checkfirst=True)
        
        contractstatustype = postgresql.ENUM('Active', 'Expired', 'Terminated', name='contractstatustype')
        contractstatustype.create(op.get_bind(), checkfirst=True)
        
        contractterminationtype = postgresql.ENUM('Yes', 'No', name='contractterminationtype')
        contractterminationtype.create(op.get_bind(), checkfirst=True)
        
        userrole = postgresql.ENUM('Contract Admin', 'Contract Manager', 'Contract Manager Backup', name='userrole')
        userrole.create(op.get_bind(), checkfirst=True)
    
    # Create tables in dependency order
    
    # 1. Vendors table (no dependencies)
    op.create_table('vendors',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vendor_id', sa.String(length=10), nullable=False),
        sa.Column('vendor_name', sa.String(length=255), nullable=False),
        sa.Column('vendor_contact_person', sa.String(length=255), nullable=False),
        sa.Column('vendor_country', sa.String(length=100), nullable=False),
        sa.Column('material_outsourcing_arrangement', _get_enum_type('Yes', 'No', name='materialoutsourcingtype', create_type=False), nullable=False),
        sa.Column('bank_customer', _get_enum_type('Aruba Bank', 'Orco Bank', 'None', name='bankcustomertype', create_type=False), nullable=False),
        sa.Column('cif', sa.String(length=6), nullable=True),
        sa.Column('due_diligence_required', _get_enum_type('Yes', 'No', name='duediligencerequiredtype', create_type=False), nullable=False),
        sa.Column('last_due_diligence_date', sa.DateTime(), nullable=True),
        sa.Column('next_required_due_diligence_date', sa.DateTime(), nullable=True),
        sa.Column('next_required_due_diligence_alert_frequency', _get_enum_type('15 days', '30 days', '60 days', '90 days', '120 days', name='alertfrequencytype', create_type=False), nullable=True),
        sa.Column('status', _get_enum_type('Active', 'Inactive', name='vendorstatustype', create_type=False), nullable=False),
        sa.Column('last_modified_by', sa.String(length=255), nullable=True),
        sa.Column('last_modified_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vendors_id'), 'vendors', ['id'], unique=False)
    op.create_index(op.f('ix_vendors_vendor_id'), 'vendors', ['vendor_id'], unique=True)
    
    # 2. Vendor related tables
    op.create_table('vendor_addresses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vendor_id', sa.Integer(), nullable=False),
        sa.Column('address', sa.Text(), nullable=False),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('state', sa.String(length=100), nullable=True),
        sa.Column('zip_code', sa.String(length=20), nullable=True),
        sa.Column('is_primary', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['vendor_id'], ['vendors.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vendor_addresses_id'), 'vendor_addresses', ['id'], unique=False)
    
    op.create_table('vendor_emails',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vendor_id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('is_primary', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['vendor_id'], ['vendors.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vendor_emails_id'), 'vendor_emails', ['id'], unique=False)
    
    op.create_table('vendor_phones',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vendor_id', sa.Integer(), nullable=False),
        sa.Column('area_code', sa.String(length=10), nullable=False),
        sa.Column('phone_number', sa.String(length=20), nullable=False),
        sa.Column('is_primary', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['vendor_id'], ['vendors.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vendor_phones_id'), 'vendor_phones', ['id'], unique=False)
    
    op.create_table('vendor_documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vendor_id', sa.Integer(), nullable=False),
        sa.Column('document_type', _get_enum_type('Due Diligence', 'Non-Disclosure Agreement', 'Integrity Policy', 'Risk Assessment Form', 'Business Continuity Plan', 'Disaster Recovery Plan', 'Insurance Policy', name='documenttype', create_type=False), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('custom_document_name', sa.String(length=255), nullable=False),
        sa.Column('document_signed_date', sa.DateTime(), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('content_type', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['vendor_id'], ['vendors.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vendor_documents_id'), 'vendor_documents', ['id'], unique=False)
    
    # 3. Users table (no dependencies)
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(length=20), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('department', _get_enum_type('Human Resources', 'Finance', 'IT', 'Operations', 'Legal', 'Marketing', 'Sales', 'Customer Service', 'Risk Management', 'Compliance', 'Audit', 'Treasury', 'Credit', 'Retail Banking', 'Corporate Banking', name='departmenttype', create_type=False), nullable=False),
        sa.Column('position', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('hashed_password', sa.String(length=255), nullable=True),
        sa.Column('role', _get_enum_type('Contract Admin', 'Contract Manager', 'Contract Manager Backup', name='userrole', create_type=False), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_user_id'), 'users', ['user_id'], unique=True)
    
    # 4. Contracts table (depends on vendors and users)
    op.create_table('contracts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('contract_id', sa.String(length=20), nullable=False),
        sa.Column('vendor_id', sa.Integer(), nullable=False),
        sa.Column('contract_description', sa.String(length=100), nullable=False),
        sa.Column('contract_type', _get_enum_type('Service Agreement', 'Maintenance Contract', 'Software License', 'Consulting Agreement', 'Support Contract', 'Lease Agreement', 'Purchase Agreement', 'Non-Disclosure Agreement', 'Partnership Agreement', 'Outsourcing Agreement', name='contracttype', create_type=False), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('automatic_renewal', _get_enum_type('Yes', 'No', name='automaticrenewaltype', create_type=False), nullable=False),
        sa.Column('renewal_period', _get_enum_type('1 Year', '2 Years', '3 Years', name='renewalperiodtype', create_type=False), nullable=True),
        sa.Column('department', _get_enum_type('Human Resources', 'Finance', 'IT', 'Operations', 'Legal', 'Marketing', 'Sales', 'Customer Service', 'Risk Management', 'Compliance', 'Audit', 'Treasury', 'Credit', 'Retail Banking', 'Corporate Banking', name='departmenttype', create_type=False), nullable=False),
        sa.Column('contract_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('contract_currency', _get_enum_type('AWG', 'XCG', 'USD', 'EUR', name='currencytype', create_type=False), nullable=False),
        sa.Column('payment_method', _get_enum_type('Invoice', 'Standing Order', name='paymentmethodtype', create_type=False), nullable=False),
        sa.Column('termination_notice_period', _get_enum_type('15 days', '30 days', '60 days', '90 days', '120 days', name='noticeperiodtype', create_type=False), nullable=False),
        sa.Column('expiration_notice_frequency', _get_enum_type('15 days', '30 days', '60 days', '90 days', '120 days', name='expirationnoticeperiodtype', create_type=False), nullable=False),
        sa.Column('contract_owner_id', sa.Integer(), nullable=False),
        sa.Column('contract_owner_backup_id', sa.Integer(), nullable=False),
        sa.Column('contract_owner_manager_id', sa.Integer(), nullable=False),
        sa.Column('status', _get_enum_type('Active', 'Expired', 'Terminated', name='contractstatustype', create_type=False), nullable=False),
        sa.Column('contract_termination', _get_enum_type('Yes', 'No', name='contractterminationtype', create_type=False), nullable=True),
        sa.Column('last_modified_by', sa.String(length=255), nullable=True),
        sa.Column('last_modified_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['contract_owner_backup_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['contract_owner_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['contract_owner_manager_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['vendor_id'], ['vendors.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_contracts_contract_id'), 'contracts', ['contract_id'], unique=True)
    op.create_index(op.f('ix_contracts_id'), 'contracts', ['id'], unique=False)
    
    # 5. Contract documents table (depends on contracts)
    op.create_table('contract_documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('contract_id', sa.Integer(), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('custom_document_name', sa.String(length=255), nullable=False),
        sa.Column('document_signed_date', sa.Date(), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('content_type', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['contract_id'], ['contracts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_contract_documents_id'), 'contract_documents', ['id'], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    dialect_name = bind.dialect.name
    
    # Drop tables in reverse order
    op.drop_index(op.f('ix_contract_documents_id'), table_name='contract_documents')
    op.drop_table('contract_documents')
    
    op.drop_index(op.f('ix_contracts_id'), table_name='contracts')
    op.drop_index(op.f('ix_contracts_contract_id'), table_name='contracts')
    op.drop_table('contracts')
    
    op.drop_index(op.f('ix_users_user_id'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    
    op.drop_index(op.f('ix_vendor_documents_id'), table_name='vendor_documents')
    op.drop_table('vendor_documents')
    
    op.drop_index(op.f('ix_vendor_phones_id'), table_name='vendor_phones')
    op.drop_table('vendor_phones')
    
    op.drop_index(op.f('ix_vendor_emails_id'), table_name='vendor_emails')
    op.drop_table('vendor_emails')
    
    op.drop_index(op.f('ix_vendor_addresses_id'), table_name='vendor_addresses')
    op.drop_table('vendor_addresses')
    
    op.drop_index(op.f('ix_vendors_vendor_id'), table_name='vendors')
    op.drop_index(op.f('ix_vendors_id'), table_name='vendors')
    op.drop_table('vendors')
    
    # Drop all enum types (PostgreSQL only)
    if dialect_name == 'postgresql':
        postgresql.ENUM(name='userrole').drop(op.get_bind(), checkfirst=True)
        postgresql.ENUM(name='contractterminationtype').drop(op.get_bind(), checkfirst=True)
        postgresql.ENUM(name='contractstatustype').drop(op.get_bind(), checkfirst=True)
        postgresql.ENUM(name='paymentmethodtype').drop(op.get_bind(), checkfirst=True)
        postgresql.ENUM(name='currencytype').drop(op.get_bind(), checkfirst=True)
        postgresql.ENUM(name='expirationnoticeperiodtype').drop(op.get_bind(), checkfirst=True)
        postgresql.ENUM(name='noticeperiodtype').drop(op.get_bind(), checkfirst=True)
        postgresql.ENUM(name='departmenttype').drop(op.get_bind(), checkfirst=True)
        postgresql.ENUM(name='renewalperiodtype').drop(op.get_bind(), checkfirst=True)
        postgresql.ENUM(name='automaticrenewaltype').drop(op.get_bind(), checkfirst=True)
        postgresql.ENUM(name='contracttype').drop(op.get_bind(), checkfirst=True)
        postgresql.ENUM(name='documenttype').drop(op.get_bind(), checkfirst=True)
        postgresql.ENUM(name='vendorstatustype').drop(op.get_bind(), checkfirst=True)
        postgresql.ENUM(name='alertfrequencytype').drop(op.get_bind(), checkfirst=True)
        postgresql.ENUM(name='duediligencerequiredtype').drop(op.get_bind(), checkfirst=True)
        postgresql.ENUM(name='bankcustomertype').drop(op.get_bind(), checkfirst=True)
        postgresql.ENUM(name='materialoutsourcingtype').drop(op.get_bind(), checkfirst=True)