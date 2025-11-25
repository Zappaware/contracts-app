from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional, List
from datetime import datetime, date
import re

from app.models.vendor import (
    BankCustomerType, MaterialOutsourcingType, DueDiligenceRequiredType,
    AlertFrequencyType, DocumentType, VendorStatusType
)
from app.core.constants import (
    ErrorMessages,
    ValidationPatterns,
    Limits
)


# Address Schemas
class VendorAddressCreate(BaseModel):
    address: str = Field(..., min_length=1)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    zip_code: Optional[str] = Field(None, max_length=20)
    is_primary: bool = False


class VendorAddressResponse(BaseModel):
    id: int
    address: str
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    is_primary: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Email Schemas
class VendorEmailCreate(BaseModel):
    email: EmailStr = Field(..., max_length=Limits.MAX_EMAIL_LENGTH)
    is_primary: bool = False


class VendorEmailResponse(BaseModel):
    id: int
    email: str
    is_primary: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Phone Schemas
class VendorPhoneCreate(BaseModel):
    area_code: str = Field(..., min_length=1, max_length=10)
    phone_number: str = Field(..., min_length=1, max_length=20)
    is_primary: bool = False

    @validator('phone_number')
    def validate_phone_number(cls, v):
        if not v or not v.strip():
            raise ValueError(ErrorMessages.INVALID_PHONE_FORMAT)
        if not re.match(ValidationPatterns.PHONE_NUMBER, v):
            raise ValueError(ErrorMessages.INVALID_PHONE_FORMAT)
        cleaned = v.replace(' ', '').replace('-', '')
        if not cleaned:
            raise ValueError(ErrorMessages.INVALID_PHONE_FORMAT)
        return v


class VendorPhoneResponse(BaseModel):
    id: int
    area_code: str
    phone_number: str
    is_primary: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Document Schemas
class VendorDocumentUpload(BaseModel):
    document_type: DocumentType
    custom_document_name: str = Field(..., min_length=1, max_length=255)
    document_signed_date: datetime


class VendorDocumentResponse(BaseModel):
    id: int
    document_type: DocumentType
    file_name: str
    custom_document_name: str
    document_signed_date: datetime
    file_path: str
    file_size: int
    content_type: str
    created_at: datetime

    class Config:
        from_attributes = True


# Main Vendor Schemas
class VendorCreate(BaseModel):
    vendor_name: str = Field(..., min_length=1, max_length=Limits.MAX_VENDOR_NAME_LENGTH)
    vendor_contact_person: str = Field(..., min_length=1, max_length=Limits.MAX_VENDOR_NAME_LENGTH)
    vendor_country: str = Field(..., min_length=1, max_length=100)
    material_outsourcing_arrangement: MaterialOutsourcingType
    bank_customer: BankCustomerType
    cif: Optional[str] = Field(None, min_length=6, max_length=6)
    due_diligence_required: DueDiligenceRequiredType
    last_due_diligence_date: Optional[datetime] = None
    next_required_due_diligence_date: Optional[datetime] = None
    next_required_due_diligence_alert_frequency: Optional[AlertFrequencyType] = None

    # Related data
    addresses: List[VendorAddressCreate] = Field(..., min_items=1, max_items=Limits.MAX_VENDOR_ADDRESSES)
    emails: List[VendorEmailCreate] = Field(..., min_items=1, max_items=Limits.MAX_VENDOR_EMAILS)
    phones: List[VendorPhoneCreate] = Field(..., min_items=1, max_items=Limits.MAX_VENDOR_PHONES)

    @validator('vendor_name')
    def validate_vendor_name(cls, v):
        if not v or not v.strip():
            raise ValueError(ErrorMessages.VENDOR_NOT_FOUND)
        return v.strip()

    @validator('vendor_contact_person')
    def validate_vendor_contact_person(cls, v):
        if not v or not v.strip():
            raise ValueError('Please enter the vendor contact person.')
        return v.strip()

    @validator('vendor_country')
    def validate_vendor_country(cls, v):
        if not v or not v.strip():
            raise ValueError(ErrorMessages.INVALID_VENDOR_COUNTRY)
        return v.strip()

    @validator('cif')
    def validate_cif(cls, v, values):
        bank_customer = values.get('bank_customer')
        if bank_customer in [BankCustomerType.ARUBA_BANK, BankCustomerType.ORCO_BANK]:
            if not v:
                raise ValueError('CIF is required when Bank Customer is Aruba Bank or Orco Bank')
            if not re.match(ValidationPatterns.CIF, v):
                raise ValueError(ErrorMessages.INVALID_CIF_FORMAT)
        return v

    @validator('last_due_diligence_date')
    def validate_last_due_diligence_date(cls, v, values):
        due_diligence_required = values.get('due_diligence_required')
        if due_diligence_required == DueDiligenceRequiredType.YES and not v:
            raise ValueError('Please enter the Last Due Diligence date.')
        return v

    @validator('next_required_due_diligence_date')
    def validate_next_required_due_diligence_date(cls, v, values):
        due_diligence_required = values.get('due_diligence_required')
        if due_diligence_required == DueDiligenceRequiredType.YES and not v:
            raise ValueError('Please provide the Next Required Due Diligence Date')
        return v

    @validator('next_required_due_diligence_alert_frequency')
    def validate_alert_frequency(cls, v, values):
        due_diligence_required = values.get('due_diligence_required')
        if due_diligence_required == DueDiligenceRequiredType.YES and not v:
            raise ValueError('Please provide the Next Required Due Diligence Alert Frequency')
        return v


class VendorUpdate(BaseModel):
    vendor_name: Optional[str] = Field(None, min_length=1, max_length=Limits.MAX_VENDOR_NAME_LENGTH)
    vendor_contact_person: Optional[str] = Field(None, min_length=1, max_length=Limits.MAX_VENDOR_NAME_LENGTH)
    vendor_country: Optional[str] = Field(None, min_length=1, max_length=100)
    material_outsourcing_arrangement: Optional[MaterialOutsourcingType] = None
    bank_customer: Optional[BankCustomerType] = None
    cif: Optional[str] = Field(None, min_length=6, max_length=6)
    due_diligence_required: Optional[DueDiligenceRequiredType] = None
    last_due_diligence_date: Optional[datetime] = None
    next_required_due_diligence_date: Optional[datetime] = None
    next_required_due_diligence_alert_frequency: Optional[AlertFrequencyType] = None
    status: Optional[VendorStatusType] = None

    @validator('vendor_name')
    def validate_vendor_name(cls, v):
        if v is not None:
            if not v or not v.strip():
                raise ValueError('Please enter the Vendor Name')
            return v.strip()
        return v

    @validator('vendor_contact_person')
    def validate_vendor_contact_person(cls, v):
        if v is not None:
            if not v or not v.strip():
                raise ValueError('Please enter the vendor contact person.')
            return v.strip()
        return v

    @validator('cif')
    def validate_cif(cls, v):
        if v is not None:
            if not re.match(ValidationPatterns.CIF, v):
                raise ValueError(ErrorMessages.INVALID_CIF_FORMAT)
            return v
        return v


class VendorStatusUpdate(BaseModel):
    status: VendorStatusType = Field(..., description="Vendor status")


class VendorResponse(BaseModel):
    id: int
    vendor_id: str
    vendor_name: str
    vendor_contact_person: str
    vendor_country: str
    material_outsourcing_arrangement: MaterialOutsourcingType
    bank_customer: BankCustomerType
    cif: Optional[str] = None
    due_diligence_required: DueDiligenceRequiredType
    last_due_diligence_date: Optional[datetime] = None
    next_required_due_diligence_date: Optional[datetime] = None
    next_required_due_diligence_alert_frequency: Optional[AlertFrequencyType] = None
    status: VendorStatusType
    last_modified_by: Optional[str] = None
    last_modified_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VendorDetailResponse(VendorResponse):
    addresses: List[VendorAddressResponse] = []
    emails: List[VendorEmailResponse] = []
    phones: List[VendorPhoneResponse] = []
    documents: List[VendorDocumentResponse] = []

    class Config:
        from_attributes = True


# NEW SCHEMAS FOR ENHANCED ENDPOINTS

class VendorListItemResponse(BaseModel):
    """Response schema for vendor list with enhanced fields"""
    id: int
    vendor_id: str
    vendor_name: str
    vendor_contact_person: str
    email: Optional[str] = None
    next_required_due_diligence_date: Optional[datetime] = None
    status: VendorStatusType
    status_color: str = Field(..., description="Color for UI: green for Active, black for Inactive")
    is_due_diligence_overdue: bool = Field(False, description="True if due diligence is overdue")

    class Config:
        from_attributes = True


class VendorListResponse(BaseModel):
    """Paginated vendor list response"""
    vendors: List[VendorListItemResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    has_results: bool
    message: Optional[str] = None


class VendorProfileBasicInfo(BaseModel):
    """Basic vendor information shown at first glance"""
    vendor_id: str
    vendor_name: str
    status: VendorStatusType
    status_color: str
    vendor_contact_person: str
    email: Optional[str] = None
    next_required_due_diligence_date: Optional[datetime] = None
    is_due_diligence_overdue: bool
    due_diligence_highlight_color: Optional[str] = None


class VendorProfileMoreInfo(BaseModel):
    """Additional vendor information in 'More' section"""
    addresses: List[VendorAddressResponse]
    country: str
    phones: List[VendorPhoneResponse]
    emails: List[VendorEmailResponse]
    bank_customer: BankCustomerType
    cif: Optional[str] = None
    material_outsourcing_arrangement: MaterialOutsourcingType
    due_diligence_required: DueDiligenceRequiredType
    last_due_diligence_date: Optional[datetime] = None
    next_required_due_diligence_alert_frequency: Optional[AlertFrequencyType] = None
    last_modified_by: Optional[str] = None
    last_modified_date: Optional[datetime] = None
    created_at: datetime


class VendorProfileDetailResponse(BaseModel):
    """Enhanced vendor profile with basic and more info sections"""
    id: int
    basic_info: VendorProfileBasicInfo
    more_info: VendorProfileMoreInfo
    documents_count: int


class VendorDocumentGroupResponse(BaseModel):
    """Documents grouped by type"""
    documents: List[VendorDocumentResponse]
    count: int
    has_documents: bool


class VendorDocumentsResponse(BaseModel):
    """All vendor documents grouped by type"""
    due_diligence: VendorDocumentGroupResponse
    non_disclosure_agreement: VendorDocumentGroupResponse
    integrity_policy: VendorDocumentGroupResponse
    risk_assessment_form: VendorDocumentGroupResponse
    business_continuity_plan: VendorDocumentGroupResponse
    disaster_recovery_plan: VendorDocumentGroupResponse
    insurance_policy: VendorDocumentGroupResponse


class VendorContractsInfo(BaseModel):
    """Vendor contracts summary"""
    count: int
    has_contracts: bool


class VendorSupportingDocsInfo(BaseModel):
    """Supporting documents summary"""
    total_count: int
    has_documents: bool
    by_type: dict


class VendorDocumentsSummaryResponse(BaseModel):
    """Summary of vendor documents and contracts"""
    vendor_id: str
    vendor_name: str
    vendor_contracts: VendorContractsInfo
    supporting_documents: VendorSupportingDocsInfo