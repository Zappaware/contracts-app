from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal


# Base schemas
class UserBase(BaseModel):
    username: str = Field(..., max_length=50)
    email: str = Field(..., max_length=100)
    first_name: str = Field(..., max_length=50)
    last_name: str = Field(..., max_length=50)
    role: str = Field(default="user", max_length=20)
    active: bool = True


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    email: Optional[str] = Field(None, max_length=100)
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    role: Optional[str] = Field(None, max_length=20)
    active: Optional[bool] = None


class User(UserBase):
    model_config = ConfigDict(from_attributes=True)
    
    user_id: int
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


# Department schemas
class DepartmentBase(BaseModel):
    department_name: str = Field(..., max_length=100)
    department_code: str = Field(..., max_length=20)
    budget_center: Optional[str] = Field(None, max_length=50)
    manager_user_id: Optional[int] = None
    active: bool = True


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    department_name: Optional[str] = Field(None, max_length=100)
    budget_center: Optional[str] = Field(None, max_length=50)
    manager_user_id: Optional[int] = None
    active: Optional[bool] = None


class Department(DepartmentBase):
    model_config = ConfigDict(from_attributes=True)
    
    department_id: int


# Contract Type schemas
class ContractTypeBase(BaseModel):
    type_name: str = Field(..., max_length=100)
    type_code: str = Field(..., max_length=20)
    parent_type_id: Optional[int] = None
    description: Optional[str] = None
    active: bool = True


class ContractTypeCreate(ContractTypeBase):
    pass


class ContractTypeUpdate(BaseModel):
    type_name: Optional[str] = Field(None, max_length=100)
    parent_type_id: Optional[int] = None
    description: Optional[str] = None
    active: Optional[bool] = None


class ContractType(ContractTypeBase):
    model_config = ConfigDict(from_attributes=True)
    
    contract_type_id: int


# Licensor schemas
class LicensorBase(BaseModel):
    company_name: str = Field(..., max_length=200)
    tax_id: Optional[str] = Field(None, max_length=50)
    website: Optional[str] = Field(None, max_length=255)


class LicensorCreate(LicensorBase):
    pass


class LicensorUpdate(BaseModel):
    company_name: Optional[str] = Field(None, max_length=200)
    tax_id: Optional[str] = Field(None, max_length=50)
    website: Optional[str] = Field(None, max_length=255)


class Licensor(LicensorBase):
    model_config = ConfigDict(from_attributes=True)
    
    licensor_id: int
    created_at: datetime
    updated_at: datetime


# Licensor Address schemas
class LicensorAddressBase(BaseModel):
    licensor_id: int
    address_type: str = Field(..., max_length=20)  # billing, shipping, legal
    street_address_1: str = Field(..., max_length=255)
    street_address_2: Optional[str] = Field(None, max_length=255)
    city: str = Field(..., max_length=100)
    state_province: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: str = Field(..., max_length=100)
    is_primary: bool = False


class LicensorAddressCreate(LicensorAddressBase):
    pass


class LicensorAddressUpdate(BaseModel):
    address_type: Optional[str] = Field(None, max_length=20)
    street_address_1: Optional[str] = Field(None, max_length=255)
    street_address_2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state_province: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    is_primary: Optional[bool] = None


class LicensorAddress(LicensorAddressBase):
    model_config = ConfigDict(from_attributes=True)
    
    address_id: int


# Contact schemas
class ContactBase(BaseModel):
    first_name: str = Field(..., max_length=50)
    last_name: str = Field(..., max_length=50)
    email: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    position: Optional[str] = Field(None, max_length=100)
    is_primary: bool = False


class ContactCreate(ContactBase):
    pass


class ContactUpdate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    position: Optional[str] = Field(None, max_length=100)
    is_primary: Optional[bool] = None


class Contact(ContactBase):
    model_config = ConfigDict(from_attributes=True)
    
    contact_id: int
    created_at: datetime
    updated_at: datetime


# Contract schemas
class ContractBase(BaseModel):
    licensor_id: int
    contract_type_id: int
    department_id: int
    contract_number: str = Field(..., max_length=50)
    title: str = Field(..., max_length=200)
    purpose: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    status: str = Field(default="pending", max_length=20)
    initial_fee_amount: Optional[Decimal] = None
    initial_fee_currency: str = Field(default="USD", max_length=3)
    maintenance_fee_amount: Optional[Decimal] = None
    maintenance_fee_currency: str = Field(default="USD", max_length=3)
    payment_method: Optional[str] = Field(None, max_length=50)
    termination_notice_days: Optional[int] = None
    renewal_frequency_days: Optional[int] = None
    warranty_months: Optional[int] = None
    warranty_years: Optional[int] = None
    special_notes: Optional[str] = None
    due_date: Optional[date] = None
    risk_assessment: Optional[str] = Field(None, max_length=20)
    notifications_enabled: bool = True


class ContractCreate(ContractBase):
    created_by: str = Field(..., max_length=50)


class ContractUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    purpose: Optional[str] = None
    end_date: Optional[date] = None
    status: Optional[str] = Field(None, max_length=20)
    initial_fee_amount: Optional[Decimal] = None
    initial_fee_currency: Optional[str] = Field(None, max_length=3)
    maintenance_fee_amount: Optional[Decimal] = None
    maintenance_fee_currency: Optional[str] = Field(None, max_length=3)
    payment_method: Optional[str] = Field(None, max_length=50)
    termination_notice_days: Optional[int] = None
    renewal_frequency_days: Optional[int] = None
    warranty_months: Optional[int] = None
    warranty_years: Optional[int] = None
    special_notes: Optional[str] = None
    due_date: Optional[date] = None
    risk_assessment: Optional[str] = Field(None, max_length=20)
    notifications_enabled: Optional[bool] = None
    updated_by: str = Field(..., max_length=50)


class Contract(ContractBase):
    model_config = ConfigDict(from_attributes=True)
    
    contract_id: int
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: Optional[str] = None


# Contract Contact schemas
class ContractContactBase(BaseModel):
    contract_id: int
    contact_id: int
    role: str = Field(..., max_length=20)  # primary, secondary, billing, technical
    active: bool = True


class ContractContactCreate(ContractContactBase):
    pass


class ContractContactUpdate(BaseModel):
    role: Optional[str] = Field(None, max_length=20)
    active: Optional[bool] = None


class ContractContact(ContractContactBase):
    model_config = ConfigDict(from_attributes=True)


# Notification Template schemas
class NotificationTemplateBase(BaseModel):
    template_name: str = Field(..., max_length=100)
    template_type: str = Field(..., max_length=20)  # renewal, expiration, payment_due
    email_subject: str = Field(..., max_length=200)
    email_body: str
    days_before_event: int
    active: bool = True


class NotificationTemplateCreate(NotificationTemplateBase):
    pass


class NotificationTemplateUpdate(BaseModel):
    template_name: Optional[str] = Field(None, max_length=100)
    email_subject: Optional[str] = Field(None, max_length=200)
    email_body: Optional[str] = None
    days_before_event: Optional[int] = None
    active: Optional[bool] = None


class NotificationTemplate(NotificationTemplateBase):
    model_config = ConfigDict(from_attributes=True)
    
    template_id: int


# Contract Notification schemas
class ContractNotificationBase(BaseModel):
    contract_id: int
    template_id: int
    scheduled_date: datetime
    status: str = Field(default="pending", max_length=20)  # pending, sent, failed
    recipient_emails: Optional[str] = None


class ContractNotificationCreate(ContractNotificationBase):
    pass


class ContractNotificationUpdate(BaseModel):
    scheduled_date: Optional[datetime] = None
    sent_date: Optional[datetime] = None
    status: Optional[str] = Field(None, max_length=20)
    recipient_emails: Optional[str] = None


class ContractNotification(ContractNotificationBase):
    model_config = ConfigDict(from_attributes=True)
    
    notification_id: int
    sent_date: Optional[datetime] = None


# Contract Document schemas
class ContractDocumentBase(BaseModel):
    contract_id: int
    document_name: str = Field(..., max_length=255)
    document_type: str = Field(..., max_length=20)  # original, amendment, renewal
    file_path: str = Field(..., max_length=500)
    file_type: Optional[str] = Field(None, max_length=10)
    file_size: Optional[int] = None
    uploaded_by: Optional[str] = Field(None, max_length=50)
    is_active: bool = True


class ContractDocumentCreate(ContractDocumentBase):
    pass


class ContractDocumentUpdate(BaseModel):
    document_name: Optional[str] = Field(None, max_length=255)
    document_type: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None


class ContractDocument(ContractDocumentBase):
    model_config = ConfigDict(from_attributes=True)
    
    document_id: int
    upload_date: datetime


# Contract Payment schemas
class ContractPaymentBase(BaseModel):
    contract_id: int
    amount: Decimal
    currency: str = Field(default="USD", max_length=3)
    due_date: date
    payment_status: str = Field(default="pending", max_length=20)  # pending, paid, overdue, cancelled
    payment_method: Optional[str] = Field(None, max_length=50)
    reference_number: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class ContractPaymentCreate(ContractPaymentBase):
    pass


class ContractPaymentUpdate(BaseModel):
    amount: Optional[Decimal] = None
    currency: Optional[str] = Field(None, max_length=3)
    due_date: Optional[date] = None
    paid_date: Optional[date] = None
    payment_status: Optional[str] = Field(None, max_length=20)
    payment_method: Optional[str] = Field(None, max_length=50)
    reference_number: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class ContractPayment(ContractPaymentBase):
    model_config = ConfigDict(from_attributes=True)
    
    payment_id: int
    paid_date: Optional[date] = None


# Contract Audit Log schemas
class ContractAuditLogBase(BaseModel):
    contract_id: int
    action_type: str = Field(..., max_length=20)  # create, update, delete, status_change
    old_values: Optional[str] = None
    new_values: Optional[str] = None
    user_id: str = Field(..., max_length=50)
    ip_address: Optional[str] = Field(None, max_length=45)


class ContractAuditLogCreate(ContractAuditLogBase):
    pass


class ContractAuditLog(ContractAuditLogBase):
    model_config = ConfigDict(from_attributes=True)
    
    audit_id: int
    action_timestamp: datetime


# User Session schemas
class UserSessionBase(BaseModel):
    user_id: int
    session_token: str = Field(..., max_length=255)
    expires_at: datetime
    ip_address: Optional[str] = Field(None, max_length=45)
    active: bool = True


class UserSessionCreate(UserSessionBase):
    pass


class UserSession(UserSessionBase):
    model_config = ConfigDict(from_attributes=True)
    
    session_id: int
    created_at: datetime


# Health check schema
class HealthCheck(BaseModel):
    status: str = "healthy"
    timestamp: datetime
    version: str
    database: str = "connected"