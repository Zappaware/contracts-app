from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum
import re


class BankCustomerType(str, Enum):
    ARUBA_BANK = "Aruba Bank"
    ORCO_BANK = "Orco Bank"
    NONE = "None"


class MaterialOutsourcingType(str, Enum):
    YES = "Yes"
    NO = "No"


class DueDiligenceRequiredType(str, Enum):
    YES = "Yes"
    NO = "No"


class AlertFrequencyType(str, Enum):
    FIFTEEN_DAYS = "15 days"
    THIRTY_DAYS = "30 days"
    SIXTY_DAYS = "60 days"
    NINETY_DAYS = "90 days"
    ONE_TWENTY_DAYS = "120 days"


class DocumentType(str, Enum):
    DUE_DILIGENCE = "Due Diligence"
    NON_DISCLOSURE_AGREEMENT = "Non-Disclosure Agreement"
    INTEGRITY_POLICY = "Integrity Policy"
    RISK_ASSESSMENT_FORM = "Risk Assessment Form"
    BUSINESS_CONTINUITY_PLAN = "Business Continuity Plan"
    DISASTER_RECOVERY_PLAN = "Disaster Recovery Plan"
    INSURANCE_POLICY = "Insurance Policy"


class VendorAddressCreate(BaseModel):
    address: str = Field(..., min_length=1, max_length=500, description="Vendor address")
    city: Optional[str] = Field(None, max_length=100, description="City (optional for non-Aruba countries)")
    state: Optional[str] = Field(None, max_length=100, description="State (optional, dropdown for US)")
    zip_code: Optional[str] = Field(None, max_length=20, description="Zip code (optional for non-Aruba countries)")

    @validator('address')
    def validate_address(cls, v):
        if not v or not v.strip():
            raise ValueError("Please enter the vendor address")
        return v.strip()


class VendorEmailCreate(BaseModel):
    email: EmailStr = Field(..., description="Vendor email address")

    @validator('email')
    def validate_email_format(cls, v):
        if not v:
            raise ValueError("Please enter the Vendor Email Address")
        return v


class VendorPhoneCreate(BaseModel):
    area_code: str = Field(..., min_length=1, max_length=10, description="Phone area code")
    phone_number: str = Field(..., min_length=1, max_length=20, description="Phone number")

    @validator('area_code')
    def validate_area_code(cls, v):
        if not v or not v.strip():
            raise ValueError("Please enter the Vendor Phone Area Code")
        return v.strip()

    @validator('phone_number')
    def validate_phone_number(cls, v):
        if not v or not v.strip():
            raise ValueError("Please enter the Vendor Phone Number")
        # Check if it contains only spaces/dashes
        if re.match(r'^[\s\-]+$', v.strip()):
            raise ValueError("Please enter the Vendor Phone Number")
        return v.strip()


class VendorCreate(BaseModel):
    # Basic Information (Always Required)
    vendor_name: str = Field(..., min_length=1, max_length=255, description="Vendor name")
    vendor_contact_person: str = Field(..., min_length=1, max_length=255, description="Vendor contact person")
    vendor_country: str = Field(..., min_length=1, max_length=100, description="Vendor country")
    
    # Material Outsourcing (Always Required)
    material_outsourcing_arrangement: MaterialOutsourcingType = Field(..., description="Material outsourcing arrangement")
    
    # Bank Customer Information (Always Required)
    bank_customer: BankCustomerType = Field(..., description="Bank customer type")
    cif: Optional[str] = Field(None, min_length=1, max_length=6, description="CIF number (required if bank customer)")
    
    # Address Information (Always Required - at least one)
    addresses: List[VendorAddressCreate] = Field(..., min_items=1, max_items=2, description="Vendor addresses")
    
    # Email Information (Always Required - at least one)
    emails: List[VendorEmailCreate] = Field(..., min_items=1, max_items=2, description="Vendor email addresses")
    
    # Phone Information (Always Required - at least one)
    phones: List[VendorPhoneCreate] = Field(..., min_items=1, max_items=2, description="Vendor phone numbers")
    
    # Due Diligence Information (Always Required)
    due_diligence_required: DueDiligenceRequiredType = Field(..., description="Due diligence required")
    last_due_diligence_date: Optional[datetime] = Field(None, description="Last due diligence date")
    next_required_due_diligence_alert_frequency: Optional[AlertFrequencyType] = Field(None, description="Alert frequency")

    @validator('vendor_name')
    def validate_vendor_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Please enter the Vendor Name")
        return v.strip()

    @validator('vendor_contact_person')
    def validate_contact_person(cls, v):
        if not v or not v.strip():
            raise ValueError("Please enter the vendor contact person")
        return v.strip()

    @validator('vendor_country')
    def validate_vendor_country(cls, v):
        if not v or not v.strip():
            raise ValueError("Please select the vendor country")
        return v.strip()

    @validator('material_outsourcing_arrangement')
    def validate_material_outsourcing(cls, v):
        if not v:
            raise ValueError("Please indicate if vendor is considered material outsourcing arrangement")
        return v

    @validator('bank_customer')
    def validate_bank_customer(cls, v):
        if not v:
            raise ValueError("Please provide the required information")
        return v

    @validator('cif')
    def validate_cif(cls, v, values):
        bank_customer = values.get('bank_customer')
        if bank_customer in [BankCustomerType.ARUBA_BANK, BankCustomerType.ORCO_BANK]:
            if not v:
                raise ValueError("Please provide the required information")
            if not v.isdigit():
                raise ValueError("CIF must contain only numeric digits")
            if len(v) > 6:
                raise ValueError("CIF must be maximum 6 digits")
        return v

    @validator('due_diligence_required')
    def validate_due_diligence_required(cls, v):
        if not v:
            raise ValueError("Please indicate if a Due Diligence is required for this new vendor")
        return v

    @validator('last_due_diligence_date')
    def validate_last_due_diligence_date(cls, v, values):
        due_diligence_required = values.get('due_diligence_required')
        if due_diligence_required == DueDiligenceRequiredType.YES:
            if not v:
                raise ValueError("Please enter the Last Due Diligence date")
        return v

    @validator('next_required_due_diligence_alert_frequency')
    def validate_alert_frequency(cls, v, values):
        due_diligence_required = values.get('due_diligence_required')
        if due_diligence_required == DueDiligenceRequiredType.YES:
            if not v:
                raise ValueError("Please provide the Next Required Due Diligence Alert Frequency")
        return v

    @validator('addresses')
    def validate_addresses(cls, v, values):
        if not v:
            raise ValueError("At least one address is required")
        
        vendor_country = values.get('vendor_country', '').lower()
        aruba_countries = ['aruba', 'curacao', 'bonaire', 'saint martin']
        
        for address in v:
            # For Aruba and related countries, city, state, zip are not required
            if vendor_country in aruba_countries:
                if address.city or address.state or address.zip_code:
                    # These fields should be hidden for Aruba countries
                    pass
            else:
                # For other countries, these fields are optional but can be provided
                pass
        
        return v


class VendorDocumentUpload(BaseModel):
    document_type: DocumentType = Field(..., description="Type of document")
    file_name: str = Field(..., min_length=1, max_length=255, description="Original file name")
    custom_document_name: str = Field(..., min_length=1, max_length=255, description="Custom document name")
    document_signed_date: datetime = Field(..., description="Date when document was signed")
    file_size: int = Field(..., gt=0, description="File size in bytes")
    content_type: str = Field(..., description="MIME type of the file")

    @validator('content_type')
    def validate_pdf_content_type(cls, v):
        if v != 'application/pdf':
            raise ValueError("Only PDF files are allowed")
        return v

    @validator('custom_document_name')
    def validate_custom_document_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Please provide a document name")
        
        # Only allow letters, numbers, and special characters: -, |, &
        import re
        if not re.match(r'^[a-zA-Z0-9\-|&\s]+$', v.strip()):
            raise ValueError("Document name can only contain letters, numbers, spaces, and the characters: - | &")
        
        return v.strip()

    @validator('document_signed_date')
    def validate_document_signed_date(cls, v):
        if not v:
            raise ValueError("Please provide the document signed date")
        
        # Check if date is not in the future
        if v > datetime.now():
            raise ValueError("Document signed date cannot be in the future")
        
        return v


class VendorResponse(BaseModel):
    id: int
    vendor_id: str
    vendor_name: str
    vendor_contact_person: str
    vendor_country: str
    material_outsourcing_arrangement: MaterialOutsourcingType
    bank_customer: BankCustomerType
    cif: Optional[str]
    due_diligence_required: DueDiligenceRequiredType
    last_due_diligence_date: Optional[datetime]
    next_required_due_diligence_date: Optional[datetime]
    next_required_due_diligence_alert_frequency: Optional[AlertFrequencyType]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VendorAddressResponse(BaseModel):
    id: int
    address: str
    city: Optional[str]
    state: Optional[str]
    zip_code: Optional[str]
    is_primary: bool

    class Config:
        from_attributes = True


class VendorEmailResponse(BaseModel):
    id: int
    email: str
    is_primary: bool

    class Config:
        from_attributes = True


class VendorPhoneResponse(BaseModel):
    id: int
    area_code: str
    phone_number: str
    is_primary: bool

    class Config:
        from_attributes = True


class VendorDocumentResponse(BaseModel):
    id: int
    document_type: DocumentType
    file_name: str
    custom_document_name: str
    document_signed_date: datetime
    file_size: int
    content_type: str
    created_at: datetime

    class Config:
        from_attributes = True


class VendorDetailResponse(VendorResponse):
    addresses: List[VendorAddressResponse]
    emails: List[VendorEmailResponse]
    phones: List[VendorPhoneResponse]
    documents: List[VendorDocumentResponse]

    class Config:
        from_attributes = True