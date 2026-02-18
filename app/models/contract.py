from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, Numeric, Date, Text
from sqlalchemy.orm import relationship
from app.db.database import Base
from datetime import datetime, date
import enum


class ContractType(str, enum.Enum):
    SERVICE_AGREEMENT = "Service Agreement"
    MAINTENANCE_CONTRACT = "Maintenance Contract"
    SOFTWARE_LICENSE = "Software License"
    CONSULTING_AGREEMENT = "Consulting Agreement"
    SUPPORT_CONTRACT = "Support Contract"
    LEASE_AGREEMENT = "Lease Agreement"
    PURCHASE_AGREEMENT = "Purchase Agreement"
    NON_DISCLOSURE_AGREEMENT = "Non-Disclosure Agreement"
    PARTNERSHIP_AGREEMENT = "Partnership Agreement"
    OUTSOURCING_AGREEMENT = "Outsourcing Agreement"


class AutomaticRenewalType(str, enum.Enum):
    YES = "Yes"
    NO = "No"


class RenewalPeriodType(str, enum.Enum):
    ONE_YEAR = "1 Year"
    TWO_YEARS = "2 Years"
    THREE_YEARS = "3 Years"


class DepartmentType(str, enum.Enum):
    HUMAN_RESOURCES = "Human Resources"
    FINANCE = "Finance"
    IT = "IT"
    OPERATIONS = "Operations"
    LEGAL = "Legal"
    MARKETING = "Marketing"
    SALES = "Sales"
    CUSTOMER_SERVICE = "Customer Service"
    RISK_MANAGEMENT = "Risk Management"
    COMPLIANCE = "Compliance"
    AUDIT = "Audit"
    TREASURY = "Treasury"
    CREDIT = "Credit"
    RETAIL_BANKING = "Retail Banking"
    CORPORATE_BANKING = "Corporate Banking"


class NoticePeriodType(str, enum.Enum):
    FIFTEEN_DAYS = "15 days"
    THIRTY_DAYS = "30 days"
    SIXTY_DAYS = "60 days"
    NINETY_DAYS = "90 days"
    ONE_TWENTY_DAYS = "120 days"
    ONE_YEAR = "365 days (1 year)"


class ExpirationNoticePeriodType(str, enum.Enum):
    FIFTEEN_DAYS = "15 days"
    THIRTY_DAYS = "30 days"
    SIXTY_DAYS = "60 days"
    NINETY_DAYS = "90 days"
    ONE_TWENTY_DAYS = "120 days"
    ONE_YEAR = "365 days (1 year)"


class CurrencyType(str, enum.Enum):
    AWG = "AWG"
    XCG = "XCG"
    USD = "USD"
    EUR = "EUR"


class PaymentMethodType(str, enum.Enum):
    INVOICE = "Invoice"
    STANDING_ORDER = "Standing Order"


class ContractStatusType(str, enum.Enum):
    ACTIVE = "Active"
    EXPIRED = "Expired"
    TERMINATED = "Terminated"
    PENDING_TERMINATION = "Pending Termination"


class ContractTerminationType(str, enum.Enum):
    YES = "Yes"
    NO = "No"


class UserRole(str, enum.Enum):
    CONTRACT_ADMIN = "Contract Admin"
    CONTRACT_MANAGER = "Contract Manager"
    CONTRACT_MANAGER_BACKUP = "Contract Manager Backup"
    CONTRACT_MANAGER_OWNER = "Contract Manager Owner"


class ContractUpdateStatus(str, enum.Enum):
    PENDING_REVIEW = "pending_review"
    RETURNED = "returned"
    UPDATED = "updated"
    COMPLETED = "completed"


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(String(20), unique=True, index=True, nullable=False)  # Auto-generated: CT1, CT2, etc.
    
    # Basic Contract Information
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    contract_description = Column(String(100), nullable=False)
    contract_type = Column(Enum(ContractType, values_callable=lambda x: [e.value for e in x]), nullable=False)
    
    # Contract Dates
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    
    # Renewal Information
    automatic_renewal = Column(Enum(AutomaticRenewalType, values_callable=lambda x: [e.value for e in x]), nullable=False)
    renewal_period = Column(Enum(RenewalPeriodType, values_callable=lambda x: [e.value for e in x]), nullable=True)  # Only if automatic_renewal = YES
    
    # Department and Financial Information
    department = Column(Enum(DepartmentType, values_callable=lambda x: [e.value for e in x]), nullable=False)
    contract_amount = Column(Numeric(15, 2), nullable=False)  # Supports large amounts with 2 decimal places
    contract_currency = Column(Enum(CurrencyType, values_callable=lambda x: [e.value for e in x]), nullable=False)
    payment_method = Column(Enum(PaymentMethodType, values_callable=lambda x: [e.value for e in x]), nullable=False)
    
    # Notice Periods
    termination_notice_period = Column(Enum(NoticePeriodType, values_callable=lambda x: [e.value for e in x]), nullable=False)
    expiration_notice_frequency = Column(Enum(ExpirationNoticePeriodType, values_callable=lambda x: [e.value for e in x]), nullable=False)
    
    # Contract Ownership
    contract_owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    contract_owner_backup_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    contract_owner_manager_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Status and Termination
    status = Column(Enum(ContractStatusType, values_callable=lambda x: [e.value for e in x]), nullable=False, default=ContractStatusType.ACTIVE)
    contract_termination = Column(Enum(ContractTerminationType, values_callable=lambda x: [e.value for e in x]), nullable=True)
    
    # Audit Trail
    last_modified_by = Column(String(255), nullable=True)
    last_modified_date = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    vendor = relationship("Vendor", back_populates="contracts")
    contract_owner = relationship("User", foreign_keys=[contract_owner_id], back_populates="owned_contracts")
    contract_owner_backup = relationship("User", foreign_keys=[contract_owner_backup_id], back_populates="backup_contracts")
    contract_owner_manager = relationship("User", foreign_keys=[contract_owner_manager_id], back_populates="managed_contracts")
    documents = relationship("ContractDocument", back_populates="contract", cascade="all, delete-orphan")
    termination_documents = relationship("TerminationDocument", back_populates="contract", cascade="all, delete-orphan")
    updates = relationship("ContractUpdate", back_populates="contract", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(20), unique=True, index=True, nullable=False)  # U1, U2, etc.
    
    # User Information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    department = Column(Enum(DepartmentType, values_callable=lambda x: [e.value for e in x]), nullable=False)
    position = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Authentication
    hashed_password = Column(String(255), nullable=True)
    role = Column(
        Enum(UserRole, values_callable=lambda x: [e.value for e in x]),
        nullable=True,
        default=UserRole.CONTRACT_MANAGER
    )
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owned_contracts = relationship("Contract", foreign_keys="Contract.contract_owner_id", back_populates="contract_owner")
    backup_contracts = relationship("Contract", foreign_keys="Contract.contract_owner_backup_id", back_populates="contract_owner_backup")
    managed_contracts = relationship("Contract", foreign_keys="Contract.contract_owner_manager_id", back_populates="contract_owner_manager")


class ContractDocument(Base):
    __tablename__ = "contract_documents"

    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)
    
    # Document Information
    file_name = Column(String(255), nullable=False)
    custom_document_name = Column(String(255), nullable=False)  # User-defined document name
    document_signed_date = Column(Date, nullable=False)  # Date when document was signed
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    content_type = Column(String(100), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    contract = relationship("Contract", back_populates="documents")


class TerminationDocument(Base):
    """Termination documents linked to a contract (separate from main contract documents)."""
    __tablename__ = "termination_documents"

    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)
    
    # Document Information
    file_name = Column(String(255), nullable=False)
    document_name = Column(String(255), nullable=False)  # User-defined display name
    document_date = Column(Date, nullable=False)  # Document date (per AC)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    content_type = Column(String(100), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    contract = relationship("Contract", back_populates="termination_documents")


class ContractUpdate(Base):
    """Track contract review workflow - responses, returns, and admin comments"""
    __tablename__ = "contract_updates"
    
    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)
    
    # Status tracking
    status = Column(Enum(ContractUpdateStatus, values_callable=lambda x: [e.value for e in x]), nullable=False, default=ContractUpdateStatus.PENDING_REVIEW)
    
    # Who provided the response
    response_provided_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Contract Manager or Backup
    response_date = Column(DateTime, nullable=True)
    has_document = Column(Boolean, default=False)

    # Decision provided by Contract Manager / Backup / Owner
    decision = Column(String(50), nullable=True)  # e.g., "Extend" / "Terminate"
    decision_comments = Column(Text, nullable=True)  # comments provided by the user who took action
    
    # Admin review (if returned)
    admin_comments = Column(Text, nullable=True)  # View-only comments from Contract Admin
    returned_reason = Column(Text, nullable=True)  # Reason for return
    returned_date = Column(DateTime, nullable=True)
    
    # Previous response info (for tracking corrections)
    previous_update_id = Column(Integer, ForeignKey("contract_updates.id"), nullable=True)  # Reference to previous update if this is a correction
    correction_date = Column(DateTime, nullable=True)
    
    # Initial values (pre-populated when editing returned contracts)
    initial_vendor_name = Column(String(255), nullable=True)
    initial_contract_type = Column(String(100), nullable=True)
    initial_description = Column(Text, nullable=True)
    initial_expiration_date = Column(Date, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    contract = relationship("Contract", back_populates="updates")
    response_provided_by = relationship("User", foreign_keys=[response_provided_by_user_id])
    previous_update = relationship("ContractUpdate", remote_side=[id], foreign_keys=[previous_update_id])