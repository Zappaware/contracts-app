from sqlalchemy import Column, Integer, String, Text, Date, DateTime, Decimal, Boolean, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from app.db.database import Base


class User(Base):
    __tablename__ = "users"
    
    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    role = Column(String(20), nullable=False, default="user")  # admin, manager, user, readonly
    active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=func.getdate())
    updated_at = Column(DateTime, default=func.getdate(), onupdate=func.getdate())
    
    # Relationships
    managed_departments = relationship("Department", back_populates="manager")
    sessions = relationship("UserSession", back_populates="user")


class UserSession(Base):
    __tablename__ = "user_sessions"
    
    session_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    session_token = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime, default=func.getdate())
    expires_at = Column(DateTime, nullable=False)
    ip_address = Column(String(45))
    active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")


class Department(Base):
    __tablename__ = "departments"
    
    department_id = Column(Integer, primary_key=True, index=True)
    department_name = Column(String(100), nullable=False)
    department_code = Column(String(20), nullable=False, unique=True)
    budget_center = Column(String(50))
    manager_user_id = Column(Integer, ForeignKey("users.user_id"))
    active = Column(Boolean, default=True)
    
    # Relationships
    manager = relationship("User", back_populates="managed_departments")
    contracts = relationship("Contract", back_populates="department")


class ContractType(Base):
    __tablename__ = "contract_types"
    
    contract_type_id = Column(Integer, primary_key=True, index=True)
    type_name = Column(String(100), nullable=False)
    type_code = Column(String(20), nullable=False, unique=True)
    parent_type_id = Column(Integer, ForeignKey("contract_types.contract_type_id"))
    description = Column(Text)
    active = Column(Boolean, default=True)
    
    # Self-referential relationship for hierarchy
    parent = relationship("ContractType", remote_side=[contract_type_id])
    children = relationship("ContractType")
    contracts = relationship("Contract", back_populates="contract_type")


class Licensor(Base):
    __tablename__ = "licensors"
    
    licensor_id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(200), nullable=False)
    tax_id = Column(String(50), unique=True)
    website = Column(String(255))
    created_at = Column(DateTime, default=func.getdate())
    updated_at = Column(DateTime, default=func.getdate(), onupdate=func.getdate())
    
    # Relationships
    addresses = relationship("LicensorAddress", back_populates="licensor")
    contracts = relationship("Contract", back_populates="licensor")


class LicensorAddress(Base):
    __tablename__ = "licensor_addresses"
    
    address_id = Column(Integer, primary_key=True, index=True)
    licensor_id = Column(Integer, ForeignKey("licensors.licensor_id"), nullable=False)
    address_type = Column(String(20), nullable=False)  # billing, shipping, legal
    street_address_1 = Column(String(255), nullable=False)
    street_address_2 = Column(String(255))
    city = Column(String(100), nullable=False)
    state_province = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(100), nullable=False)
    is_primary = Column(Boolean, default=False)
    
    # Relationships
    licensor = relationship("Licensor", back_populates="addresses")


class Contact(Base):
    __tablename__ = "contacts"
    
    contact_id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100))
    phone = Column(String(20))
    position = Column(String(100))
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.getdate())
    updated_at = Column(DateTime, default=func.getdate(), onupdate=func.getdate())
    
    # Relationships
    contract_contacts = relationship("ContractContact", back_populates="contact")


class Contract(Base):
    __tablename__ = "contracts"
    
    contract_id = Column(Integer, primary_key=True, index=True)
    licensor_id = Column(Integer, ForeignKey("licensors.licensor_id"), nullable=False)
    contract_type_id = Column(Integer, ForeignKey("contract_types.contract_type_id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.department_id"), nullable=False)
    contract_number = Column(String(50), unique=True, nullable=False)
    title = Column(String(200), nullable=False)
    purpose = Column(Text)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    status = Column(String(20), nullable=False, default="pending")  # active, expired, terminated, pending
    initial_fee_amount = Column(Decimal(15, 2))
    initial_fee_currency = Column(String(3), default="USD")
    maintenance_fee_amount = Column(Decimal(15, 2))
    maintenance_fee_currency = Column(String(3), default="USD")
    payment_method = Column(String(50))
    termination_notice_days = Column(Integer)
    renewal_frequency_days = Column(Integer)
    warranty_months = Column(Integer)
    warranty_years = Column(Integer)
    special_notes = Column(Text)
    due_date = Column(Date)
    risk_assessment = Column(String(20))
    notifications_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.getdate())
    updated_at = Column(DateTime, default=func.getdate(), onupdate=func.getdate())
    created_by = Column(String(50))
    updated_by = Column(String(50))
    
    # Relationships
    licensor = relationship("Licensor", back_populates="contracts")
    contract_type = relationship("ContractType", back_populates="contracts")
    department = relationship("Department", back_populates="contracts")
    contract_contacts = relationship("ContractContact", back_populates="contract")
    notifications = relationship("ContractNotification", back_populates="contract")
    documents = relationship("ContractDocument", back_populates="contract")
    payments = relationship("ContractPayment", back_populates="contract")
    audit_logs = relationship("ContractAuditLog", back_populates="contract")


class ContractContact(Base):
    __tablename__ = "contract_contacts"
    
    contract_id = Column(Integer, ForeignKey("contracts.contract_id"), primary_key=True)
    contact_id = Column(Integer, ForeignKey("contacts.contact_id"), primary_key=True)
    role = Column(String(20), nullable=False)  # primary, secondary, billing, technical
    active = Column(Boolean, default=True)
    
    # Relationships
    contract = relationship("Contract", back_populates="contract_contacts")
    contact = relationship("Contact", back_populates="contract_contacts")


class NotificationTemplate(Base):
    __tablename__ = "notification_templates"
    
    template_id = Column(Integer, primary_key=True, index=True)
    template_name = Column(String(100), nullable=False)
    template_type = Column(String(20), nullable=False)  # renewal, expiration, payment_due
    email_subject = Column(String(200), nullable=False)
    email_body = Column(Text, nullable=False)
    days_before_event = Column(Integer, nullable=False)
    active = Column(Boolean, default=True)
    
    # Relationships
    notifications = relationship("ContractNotification", back_populates="template")


class ContractNotification(Base):
    __tablename__ = "contract_notifications"
    
    notification_id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.contract_id"), nullable=False)
    template_id = Column(Integer, ForeignKey("notification_templates.template_id"), nullable=False)
    scheduled_date = Column(DateTime, nullable=False)
    sent_date = Column(DateTime)
    status = Column(String(20), nullable=False, default="pending")  # pending, sent, failed
    recipient_emails = Column(Text)
    
    # Relationships
    contract = relationship("Contract", back_populates="notifications")
    template = relationship("NotificationTemplate", back_populates="notifications")


class ContractDocument(Base):
    __tablename__ = "contract_documents"
    
    document_id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.contract_id"), nullable=False)
    document_name = Column(String(255), nullable=False)
    document_type = Column(String(20), nullable=False)  # original, amendment, renewal
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(10))
    file_size = Column(BigInteger)
    upload_date = Column(DateTime, default=func.getdate())
    uploaded_by = Column(String(50))
    is_active = Column(Boolean, default=True)
    
    # Relationships
    contract = relationship("Contract", back_populates="documents")


class ContractPayment(Base):
    __tablename__ = "contract_payments"
    
    payment_id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.contract_id"), nullable=False)
    amount = Column(Decimal(15, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    due_date = Column(Date, nullable=False)
    paid_date = Column(Date)
    payment_status = Column(String(20), nullable=False, default="pending")  # pending, paid, overdue, cancelled
    payment_method = Column(String(50))
    reference_number = Column(String(100))
    notes = Column(Text)
    
    # Relationships
    contract = relationship("Contract", back_populates="payments")


class ContractAuditLog(Base):
    __tablename__ = "contract_audit_log"
    
    audit_id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.contract_id"), nullable=False)
    action_type = Column(String(20), nullable=False)  # create, update, delete, status_change
    old_values = Column(Text)
    new_values = Column(Text)
    user_id = Column(String(50), nullable=False)
    action_timestamp = Column(DateTime, default=func.getdate())
    ip_address = Column(String(45))
    
    # Relationships
    contract = relationship("Contract", back_populates="audit_logs")