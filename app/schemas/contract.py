from pydantic import BaseModel, Field, validator, EmailStr
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal
import re

from app.models.contract import (
    ContractType, AutomaticRenewalType, RenewalPeriodType, DepartmentType,
    NoticePeriodType, ExpirationNoticePeriodType, CurrencyType, PaymentMethodType,
    ContractStatusType, ContractTerminationType
)


# User Schemas
class UserBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100, description="User's first name")
    last_name: str = Field(..., min_length=1, max_length=100, description="User's last name")
    email: EmailStr = Field(..., description="User's email address")
    department: DepartmentType = Field(..., description="User's department")
    position: str = Field(..., min_length=1, max_length=100, description="User's position")


class UserCreate(UserBase):
    pass


class UserResponse(UserBase):
    id: int
    user_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    id: int
    user_id: str
    first_name: str
    last_name: str
    email: EmailStr
    department: DepartmentType
    position: str
    is_active: bool

    class Config:
        from_attributes = True

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


# Contract Document Schemas
class ContractDocumentBase(BaseModel):
    custom_document_name: str = Field(..., min_length=1, max_length=255, description="Custom name for the document")
    document_signed_date: date = Field(..., description="Date when document was signed")

    @validator('custom_document_name')
    def validate_custom_document_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Document name cannot be empty')
        
        # Only allow letters, numbers, spaces, and special characters: -, |, & (hyphen at start of class so literal)
        if not re.match(r'^[-a-zA-Z0-9|&\s]+$', v.strip()):
            raise ValueError('Document name can only contain letters, numbers, spaces, and the characters: - | &')
        
        return v.strip()

    @validator('document_signed_date')
    def validate_document_signed_date(cls, v):
        if v > date.today():
            raise ValueError('Document signed date cannot be in the future')
        return v


class ContractDocumentResponse(ContractDocumentBase):
    id: int
    file_name: str
    file_path: str
    file_size: int
    content_type: str
    created_at: datetime

    class Config:
        from_attributes = True


# Termination Document Schemas
class TerminationDocumentBase(BaseModel):
    document_name: str = Field(..., min_length=1, max_length=255, description="Display name for the termination document")
    document_date: date = Field(..., description="Document date")

    @validator("document_name")
    def validate_document_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Document name cannot be empty")
        if not re.match(r"^[-a-zA-Z0-9|&\s]+$", v.strip()):
            raise ValueError("Document name can only contain letters, numbers, spaces, and the characters: - | &")
        return v.strip()

    @validator("document_date")
    def validate_document_date(cls, v):
        if v > date.today():
            raise ValueError("Document date cannot be in the future")
        return v


class TerminationDocumentResponse(TerminationDocumentBase):
    id: int
    contract_id: int
    file_name: str
    file_path: str
    file_size: int
    content_type: str
    created_at: datetime

    class Config:
        from_attributes = True


class TerminationDocumentUpdate(BaseModel):
    """Optional fields for updating a termination document."""
    document_name: Optional[str] = Field(None, min_length=1, max_length=255)
    document_date: Optional[date] = None


class TerminationDocumentFromContractDocument(BaseModel):
    """Create a termination document by copying an existing contract document (e.g. on Complete Terminate)."""
    contract_document_id: int = Field(..., gt=0)
    document_date: date = Field(...)


# Contract Schemas
class ContractBase(BaseModel):
    vendor_id: int = Field(..., gt=0, description="ID of the vendor")
    contract_description: str = Field(..., min_length=1, max_length=100, description="Contract description")
    contract_type: ContractType = Field(..., description="Type of contract")
    start_date: date = Field(..., description="Contract start date")
    end_date: date = Field(..., description="Contract end date")
    automatic_renewal: AutomaticRenewalType = Field(..., description="Whether contract has automatic renewal")
    renewal_period: Optional[RenewalPeriodType] = Field(None, description="Renewal period if automatic renewal is Yes")
    department: DepartmentType = Field(..., description="Department responsible for the contract")
    contract_amount: Decimal = Field(..., gt=0, max_digits=15, decimal_places=2, description="Contract amount")
    contract_currency: CurrencyType = Field(..., description="Contract currency")
    payment_method: PaymentMethodType = Field(..., description="Payment method")
    termination_notice_period: NoticePeriodType = Field(..., description="Termination notice period")
    expiration_notice_frequency: ExpirationNoticePeriodType = Field(..., description="Expiration notice frequency")
    contract_owner_id: int = Field(..., gt=0, description="ID of the contract owner")
    contract_owner_backup_id: int = Field(..., gt=0, description="ID of the contract owner backup")
    contract_owner_manager_id: int = Field(..., gt=0, description="ID of the contract owner manager")

    @validator('contract_description')
    def validate_contract_description(cls, v):
        if not v or not v.strip():
            raise ValueError('Please indicate the Contract Description.')
        
        # Only allow letters, digits and special characters: / - & ( ): % #
        if not re.match(r'^[a-zA-Z0-9\s/\-&():% #]+$', v.strip()):
            raise ValueError('Contract Description can only contain letters, digits and the characters: / - & ( ): % #')
        
        return v.strip()

    @validator('end_date')
    def validate_end_date(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('Contract end date must be after start date')
        return v

    @validator('renewal_period')
    def validate_renewal_period(cls, v, values):
        if 'automatic_renewal' in values:
            if values['automatic_renewal'] == AutomaticRenewalType.YES and v is None:
                raise ValueError('Renewal period is required when automatic renewal is Yes')
            if values['automatic_renewal'] == AutomaticRenewalType.NO and v is not None:
                raise ValueError('Renewal period should not be provided when automatic renewal is No')
        return v

    @validator('contract_amount')
    def validate_contract_amount(cls, v):
        if v <= 0:
            raise ValueError('Please enter the Contract Amount')
        # Additional validation could be added here for string input format
        # if needed to check for only numeric values and ., characters
        return v

    @validator('contract_owner_backup_id')
    def validate_different_backup(cls, v, values):
        if 'contract_owner_id' in values and v == values['contract_owner_id']:
            raise ValueError('Contract owner backup must be different from contract owner')
        return v

    @validator('contract_owner_manager_id')
    def validate_different_manager(cls, v, values):
        if 'contract_owner_id' in values and v == values['contract_owner_id']:
            raise ValueError('Contract owner manager must be different from contract owner')
        if 'contract_owner_backup_id' in values and v == values['contract_owner_backup_id']:
            raise ValueError('Contract owner manager must be different from contract owner backup')
        return v


class ContractCreate(ContractBase):
    pass


class ContractUpdate(BaseModel):
    contract_description: Optional[str] = Field(None, min_length=1, max_length=100)
    contract_type: Optional[ContractType] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    automatic_renewal: Optional[AutomaticRenewalType] = None
    renewal_period: Optional[RenewalPeriodType] = None
    department: Optional[DepartmentType] = None
    contract_amount: Optional[Decimal] = Field(None, gt=0)
    contract_currency: Optional[CurrencyType] = None
    payment_method: Optional[PaymentMethodType] = None
    termination_notice_period: Optional[NoticePeriodType] = None
    expiration_notice_frequency: Optional[ExpirationNoticePeriodType] = None
    contract_owner_id: Optional[int] = Field(None, gt=0)
    contract_owner_backup_id: Optional[int] = Field(None, gt=0)
    contract_owner_manager_id: Optional[int] = Field(None, gt=0)
    contract_termination: Optional[ContractTerminationType] = None
    status: Optional[ContractStatusType] = None

    @validator('contract_description')
    def validate_contract_description(cls, v):
        if v is not None:
            if not v or not v.strip():
                raise ValueError('Please indicate the Contract Description.')
            if not re.match(r'^[a-zA-Z0-9\s/\-&():% #]+$', v.strip()):
                raise ValueError('Contract Description can only contain letters, digits and the characters: / - & ( ): % #')
            return v.strip()
        return v


class ContractResponse(ContractBase):
    id: int
    contract_id: str
    status: ContractStatusType
    contract_termination: Optional[ContractTerminationType] = None
    last_modified_by: Optional[str] = None
    last_modified_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ContractDetailResponse(ContractResponse):
    # Include related data
    vendor: Optional[dict] = None  # Will be populated with vendor basic info
    contract_owner: Optional[UserListResponse] = None
    contract_owner_backup: Optional[UserListResponse] = None
    contract_owner_manager: Optional[UserListResponse] = None
    documents: List[ContractDocumentResponse] = []

    class Config:
        from_attributes = True


class ContractListResponse(BaseModel):
    id: int
    contract_id: str
    vendor_name: str
    contract_description: str
    contract_type: ContractType
    start_date: date
    end_date: date
    status: ContractStatusType
    contract_amount: Decimal
    contract_currency: CurrencyType
    department: DepartmentType
    contract_owner_name: str
    created_at: datetime

    class Config:
        from_attributes = True


class ContractSearchResponse(BaseModel):
    """
    Paginated response for contract search and filter (DSA-42)
    """
    contracts: List[ContractListResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int

    class Config:
        from_attributes = True


# Validation Schemas for Dropdowns
class ContractValidationEnums(BaseModel):
    contract_types: List[str] = [ct.value for ct in ContractType]
    automatic_renewal_types: List[str] = [art.value for art in AutomaticRenewalType]
    renewal_period_types: List[str] = [rpt.value for rpt in RenewalPeriodType]
    department_types: List[str] = [dt.value for dt in DepartmentType]
    notice_period_types: List[str] = [npt.value for npt in NoticePeriodType]
    expiration_notice_period_types: List[str] = [enpt.value for enpt in ExpirationNoticePeriodType]
    currency_types: List[str] = [ct.value for ct in CurrencyType]
    payment_method_types: List[str] = [pmt.value for pmt in PaymentMethodType]
    contract_status_types: List[str] = [cst.value for cst in ContractStatusType]
    contract_termination_types: List[str] = [ctt.value for ctt in ContractTerminationType]


# Contract Summary for Dashboard
class ContractSummary(BaseModel):
    total_contracts: int
    active_contracts: int
    expiring_soon: int  # Contracts expiring within notice period
    total_contract_value: Decimal
    contracts_by_department: dict
    contracts_by_currency: dict

    class Config:
        from_attributes = True