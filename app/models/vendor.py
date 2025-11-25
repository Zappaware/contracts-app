from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from app.db.database import Base
from datetime import datetime
import enum


class BankCustomerType(str, enum.Enum):
    ARUBA_BANK = "Aruba Bank"
    ORCO_BANK = "Orco Bank"
    NONE = "None"


class MaterialOutsourcingType(str, enum.Enum):
    YES = "Yes"
    NO = "No"


class DueDiligenceRequiredType(str, enum.Enum):
    YES = "Yes"
    NO = "No"


class AlertFrequencyType(str, enum.Enum):
    FIFTEEN_DAYS = "15 days"
    THIRTY_DAYS = "30 days"
    SIXTY_DAYS = "60 days"
    NINETY_DAYS = "90 days"
    ONE_TWENTY_DAYS = "120 days"


class VendorStatusType(str, enum.Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"


class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(String(10), unique=True, index=True, nullable=False)  # AB1, AB2, OB1, etc.
    
    # Basic Information
    vendor_name = Column(String(255), nullable=False)
    vendor_contact_person = Column(String(255), nullable=False)
    vendor_country = Column(String(100), nullable=False)
    
    # Material Outsourcing
    material_outsourcing_arrangement = Column(Enum(MaterialOutsourcingType, values_callable=lambda x: [e.value for e in x]), nullable=False)
    
    # Bank Customer Information
    bank_customer = Column(Enum(BankCustomerType, values_callable=lambda x: [e.value for e in x]), nullable=False)
    cif = Column(String(6), nullable=True)  # Only if bank customer is Aruba Bank or Orco Bank
    
    # Due Diligence Information
    due_diligence_required = Column(Enum(DueDiligenceRequiredType, values_callable=lambda x: [e.value for e in x]), nullable=False)
    last_due_diligence_date = Column(DateTime, nullable=True)
    next_required_due_diligence_date = Column(DateTime, nullable=True)
    next_required_due_diligence_alert_frequency = Column(Enum(AlertFrequencyType, values_callable=lambda x: [e.value for e in x]), nullable=True)
    
    # Status
    status = Column(Enum(VendorStatusType, values_callable=lambda x: [e.value for e in x]), nullable=False, default=VendorStatusType.ACTIVE)
    
    # Audit Trail
    last_modified_by = Column(String(255), nullable=True)
    last_modified_date = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    addresses = relationship("VendorAddress", back_populates="vendor", cascade="all, delete-orphan")
    emails = relationship("VendorEmail", back_populates="vendor", cascade="all, delete-orphan")
    phones = relationship("VendorPhone", back_populates="vendor", cascade="all, delete-orphan")
    documents = relationship("VendorDocument", back_populates="vendor", cascade="all, delete-orphan")
    contracts = relationship("Contract", back_populates="vendor", cascade="all, delete-orphan")


class VendorAddress(Base):
    __tablename__ = "vendor_addresses"

    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    
    address = Column(Text, nullable=False)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    zip_code = Column(String(20), nullable=True)
    is_primary = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    vendor = relationship("Vendor", back_populates="addresses")


class VendorEmail(Base):
    __tablename__ = "vendor_emails"

    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    
    email = Column(String(255), nullable=False)
    is_primary = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    vendor = relationship("Vendor", back_populates="emails")


class VendorPhone(Base):
    __tablename__ = "vendor_phones"

    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    
    area_code = Column(String(10), nullable=False)
    phone_number = Column(String(20), nullable=False)
    is_primary = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    vendor = relationship("Vendor", back_populates="phones")


class DocumentType(str, enum.Enum):
    DUE_DILIGENCE = "Due Diligence"
    NON_DISCLOSURE_AGREEMENT = "Non-Disclosure Agreement"
    INTEGRITY_POLICY = "Integrity Policy"
    RISK_ASSESSMENT_FORM = "Risk Assessment Form"
    BUSINESS_CONTINUITY_PLAN = "Business Continuity Plan"
    DISASTER_RECOVERY_PLAN = "Disaster Recovery Plan"
    INSURANCE_POLICY = "Insurance Policy"


class VendorDocument(Base):
    __tablename__ = "vendor_documents"

    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    
    document_type = Column(Enum(DocumentType, values_callable=lambda x: [e.value for e in x]), nullable=False)
    file_name = Column(String(255), nullable=False)
    custom_document_name = Column(String(255), nullable=False)  # User-defined document name
    document_signed_date = Column(DateTime, nullable=False)  # Date when document was signed
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    content_type = Column(String(100), nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    vendor = relationship("Vendor", back_populates="documents")