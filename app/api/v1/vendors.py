from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import json
from pydantic import ValidationError

from app.db.database import get_db
from app.services.vendor_service import VendorService
from app.schemas.vendor import (
    VendorCreate, VendorUpdate, VendorResponse, VendorDetailResponse,
    DocumentType, VendorDocumentResponse, VendorListResponse,
    VendorListItemResponse, VendorProfileDetailResponse,
    VendorProfileBasicInfo, VendorProfileMoreInfo,
    VendorDocumentsResponse, VendorDocumentsSummaryResponse,
    VendorAddressResponse, VendorEmailResponse, VendorPhoneResponse
)
from app.models.vendor import DueDiligenceRequiredType, MaterialOutsourcingType, BankCustomerType

router = APIRouter()


@router.post("/", response_model=VendorDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_vendor(
    vendor_data: str = Form(..., description="JSON string of vendor data"),
    # Due Diligence Documents (required if due_diligence_required = YES)
    due_diligence_doc: Optional[UploadFile] = File(None, description="Due Diligence document (PDF)"),
    due_diligence_name: Optional[str] = Form(None, description="Custom name for Due Diligence document"),
    due_diligence_signed_date: Optional[str] = Form(None, description="Due Diligence signed date (YYYY-MM-DD)"),
    
    non_disclosure_doc: Optional[UploadFile] = File(None, description="Non-Disclosure Agreement document (PDF)"),
    non_disclosure_name: Optional[str] = Form(None, description="Custom name for Non-Disclosure Agreement document"),
    non_disclosure_signed_date: Optional[str] = Form(None, description="Non-Disclosure Agreement signed date (YYYY-MM-DD)"),
    
    integrity_policy_doc: Optional[UploadFile] = File(None, description="Integrity Policy document (PDF, optional)"),
    integrity_policy_name: Optional[str] = Form(None, description="Custom name for Integrity Policy document"),
    integrity_policy_signed_date: Optional[str] = Form(None, description="Integrity Policy signed date (YYYY-MM-DD)"),
    
    # Risk Assessment Documents (required if material_outsourcing_arrangement = YES)
    risk_assessment_doc: Optional[UploadFile] = File(None, description="Risk Assessment Form document (PDF)"),
    risk_assessment_name: Optional[str] = Form(None, description="Custom name for Risk Assessment Form document"),
    risk_assessment_signed_date: Optional[str] = Form(None, description="Risk Assessment Form signed date (YYYY-MM-DD)"),
    
    business_continuity_doc: Optional[UploadFile] = File(None, description="Business Continuity Plan document (PDF, optional)"),
    business_continuity_name: Optional[str] = Form(None, description="Custom name for Business Continuity Plan document"),
    business_continuity_signed_date: Optional[str] = Form(None, description="Business Continuity Plan signed date (YYYY-MM-DD)"),
    
    disaster_recovery_doc: Optional[UploadFile] = File(None, description="Disaster Recovery Plan document (PDF, optional)"),
    disaster_recovery_name: Optional[str] = Form(None, description="Custom name for Disaster Recovery Plan document"),
    disaster_recovery_signed_date: Optional[str] = Form(None, description="Disaster Recovery Plan signed date (YYYY-MM-DD)"),
    
    insurance_policy_doc: Optional[UploadFile] = File(None, description="Insurance Policy document (PDF, optional)"),
    insurance_policy_name: Optional[str] = Form(None, description="Custom name for Insurance Policy document"),
    insurance_policy_signed_date: Optional[str] = Form(None, description="Insurance Policy signed date (YYYY-MM-DD)"),
    
    db: Session = Depends(get_db)
):
    """
    Create a new vendor with all required information and documents.
    
    The vendor_data should be a JSON string containing all vendor information.
    Documents are uploaded as separate files based on the vendor configuration.
    """
    try:
        # Parse vendor data from JSON string
        print(f"\n{'='*60}")
        print(f"BACKEND: Received vendor creation request")
        print(f"{'='*60}")
        print(f"Raw vendor_data: {vendor_data[:200]}...")
        
        vendor_dict = json.loads(vendor_data)
        vendor_create = VendorCreate(**vendor_dict)
        print(f"✅ Vendor data parsed successfully")
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON format in vendor_data"
        )
    except ValidationError as e:
        print(f"❌ Pydantic validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {e}"
        )
    
    vendor_service = VendorService(db)
    
    # Validate vendor creation requirements
    validation_errors = vendor_service.validate_vendor_creation_requirements(vendor_create)
    if validation_errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"errors": validation_errors}
        )
    
    # Validate required documents and their metadata
    document_errors = []
    
    # Check Due Diligence documents
    if vendor_create.due_diligence_required == DueDiligenceRequiredType.YES:
        if not due_diligence_doc:
            document_errors.append("Please upload this required document: Due Diligence")
        elif not due_diligence_name or not due_diligence_signed_date:
            document_errors.append("Please provide document name and signed date for Due Diligence")
            
        if not non_disclosure_doc:
            document_errors.append("Please upload this required document: Non-Disclosure Agreement")
        elif not non_disclosure_name or not non_disclosure_signed_date:
            document_errors.append("Please provide document name and signed date for Non-Disclosure Agreement")
    
    # Check Risk Assessment documents
    if vendor_create.material_outsourcing_arrangement == MaterialOutsourcingType.YES:
        if not risk_assessment_doc:
            document_errors.append("Please upload this required document: Risk Assessment Form")
        elif not risk_assessment_name or not risk_assessment_signed_date:
            document_errors.append("Please provide document name and signed date for Risk Assessment Form")
    
    # Check optional documents metadata
    if integrity_policy_doc and (not integrity_policy_name or not integrity_policy_signed_date):
        document_errors.append("Please provide document name and signed date for Integrity Policy")
    if business_continuity_doc and (not business_continuity_name or not business_continuity_signed_date):
        document_errors.append("Please provide document name and signed date for Business Continuity Plan")
    if disaster_recovery_doc and (not disaster_recovery_name or not disaster_recovery_signed_date):
        document_errors.append("Please provide document name and signed date for Disaster Recovery Plan")
    if insurance_policy_doc and (not insurance_policy_name or not insurance_policy_signed_date):
        document_errors.append("Please provide document name and signed date for Insurance Policy")
    
    if document_errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"errors": document_errors}
        )
    
    # Validate PDF files
    pdf_validation_errors = []
    documents_to_validate = [
        (due_diligence_doc, "Due Diligence"),
        (non_disclosure_doc, "Non-Disclosure Agreement"),
        (integrity_policy_doc, "Integrity Policy"),
        (risk_assessment_doc, "Risk Assessment Form"),
        (business_continuity_doc, "Business Continuity Plan"),
        (disaster_recovery_doc, "Disaster Recovery Plan"),
        (insurance_policy_doc, "Insurance Policy")
    ]
    
    for doc, doc_name in documents_to_validate:
        if doc and not vendor_service.validate_pdf_file(doc):
            pdf_validation_errors.append(f"Invalid PDF file for {doc_name}")
    
    if pdf_validation_errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"errors": pdf_validation_errors}
        )
    
    try:
        # Determine bank type dynamically based on bank_customer
        if vendor_create.bank_customer == BankCustomerType.ARUBA_BANK:
            bank_type = "AB"
        elif vendor_create.bank_customer == BankCustomerType.ORCO_BANK:
            bank_type = "OB"
        else:  # BankCustomerType.NONE
            bank_type = "AB"  # Default to Aruba Bank for None customers
        
        print(f"Creating vendor with bank_type: {bank_type}")
        
        # Create vendor
        vendor = vendor_service.create_vendor(vendor_create, bank_type)
        print(f"✅ Vendor created: ID={vendor.id}, vendor_id={vendor.vendor_id}")
        
        # Upload documents with custom names and signed dates
        uploaded_docs = []
        from datetime import datetime
        
        print(f"\n📄 Processing document uploads...")
        
        if due_diligence_doc:
            print(f"  Due Diligence - Name: '{due_diligence_name}', Date: '{due_diligence_signed_date}'")
            try:
                signed_date = datetime.fromisoformat(due_diligence_signed_date)
                print(f"    ✅ Date parsed: {signed_date}")
            except Exception as e:
                print(f"    ❌ Date parse error: {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid date format for due_diligence_signed_date: {due_diligence_signed_date}"
                )
            doc = await vendor_service.upload_vendor_document(
                vendor.id, due_diligence_doc, DocumentType.DUE_DILIGENCE,
                due_diligence_name, signed_date
            )
            uploaded_docs.append(doc)
        
        if non_disclosure_doc:
            print(f"  NDA - Name: '{non_disclosure_name}', Date: '{non_disclosure_signed_date}'")
            try:
                signed_date = datetime.fromisoformat(non_disclosure_signed_date)
                print(f"    ✅ Date parsed: {signed_date}")
            except Exception as e:
                print(f"    ❌ Date parse error: {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid date format for non_disclosure_signed_date: {non_disclosure_signed_date}"
                )
            doc = await vendor_service.upload_vendor_document(
                vendor.id, non_disclosure_doc, DocumentType.NON_DISCLOSURE_AGREEMENT,
                non_disclosure_name, signed_date
            )
            uploaded_docs.append(doc)
        
        if integrity_policy_doc:
            print(f"  Integrity Policy - Name: '{integrity_policy_name}', Date: '{integrity_policy_signed_date}'")
            try:
                signed_date = datetime.fromisoformat(integrity_policy_signed_date)
                print(f"    ✅ Date parsed: {signed_date}")
            except Exception as e:
                print(f"    ❌ Date parse error: {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid date format for integrity_policy_signed_date: {integrity_policy_signed_date}"
                )
            doc = await vendor_service.upload_vendor_document(
                vendor.id, integrity_policy_doc, DocumentType.INTEGRITY_POLICY,
                integrity_policy_name, signed_date
            )
            uploaded_docs.append(doc)
        
        if risk_assessment_doc:
            print(f"  Risk Assessment - Name: '{risk_assessment_name}', Date: '{risk_assessment_signed_date}'")
            try:
                signed_date = datetime.fromisoformat(risk_assessment_signed_date)
                print(f"    ✅ Date parsed: {signed_date}")
            except Exception as e:
                print(f"    ❌ Date parse error: {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid date format for risk_assessment_signed_date: {risk_assessment_signed_date}"
                )
            doc = await vendor_service.upload_vendor_document(
                vendor.id, risk_assessment_doc, DocumentType.RISK_ASSESSMENT_FORM,
                risk_assessment_name, signed_date
            )
            uploaded_docs.append(doc)
        
        if business_continuity_doc:
            print(f"  Business Continuity - Name: '{business_continuity_name}', Date: '{business_continuity_signed_date}'")
            try:
                signed_date = datetime.fromisoformat(business_continuity_signed_date)
                print(f"    ✅ Date parsed: {signed_date}")
            except Exception as e:
                print(f"    ❌ Date parse error: {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid date format for business_continuity_signed_date: {business_continuity_signed_date}"
                )
            doc = await vendor_service.upload_vendor_document(
                vendor.id, business_continuity_doc, DocumentType.BUSINESS_CONTINUITY_PLAN,
                business_continuity_name, signed_date
            )
            uploaded_docs.append(doc)
        
        if disaster_recovery_doc:
            print(f"  Disaster Recovery - Name: '{disaster_recovery_name}', Date: '{disaster_recovery_signed_date}'")
            try:
                signed_date = datetime.fromisoformat(disaster_recovery_signed_date)
                print(f"    ✅ Date parsed: {signed_date}")
            except Exception as e:
                print(f"    ❌ Date parse error: {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid date format for disaster_recovery_signed_date: {disaster_recovery_signed_date}"
                )
            doc = await vendor_service.upload_vendor_document(
                vendor.id, disaster_recovery_doc, DocumentType.DISASTER_RECOVERY_PLAN,
                disaster_recovery_name, signed_date
            )
            uploaded_docs.append(doc)
        
        if insurance_policy_doc:
            print(f"  Insurance Policy - Name: '{insurance_policy_name}', Date: '{insurance_policy_signed_date}'")
            try:
                signed_date = datetime.fromisoformat(insurance_policy_signed_date)
                print(f"    ✅ Date parsed: {signed_date}")
            except Exception as e:
                print(f"    ❌ Date parse error: {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid date format for insurance_policy_signed_date: {insurance_policy_signed_date}"
                )
            doc = await vendor_service.upload_vendor_document(
                vendor.id, insurance_policy_doc, DocumentType.INSURANCE_POLICY,
                insurance_policy_name, signed_date
            )
            uploaded_docs.append(doc)
        
        # Refresh vendor to get all related data
        print(f"Refreshing vendor data...")
        db.refresh(vendor)
        print(f"✅ Vendor creation completed successfully: {vendor.vendor_id}")
        print(f"{'='*60}\n")
        
        return vendor
        
    except HTTPException as e:
        # Re-raise HTTP exceptions as-is
        print(f"❌ HTTPException during vendor creation: {e.status_code} - {e.detail}")
        raise
    except Exception as e:
        print(f"❌ Unexpected error during vendor creation: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating vendor: {str(e)}"
        )


@router.put("/{vendor_id}", response_model=VendorResponse)
def update_vendor(
    vendor_id: int,
    vendor_data: VendorUpdate,
    modified_by: str = "SYSTEM",
    db: Session = Depends(get_db)
):
    """
    Update existing vendor with audit trail.
    The modified_by parameter can be passed as a query parameter.
    """
    vendor_service = VendorService(db)
    
    try:
        vendor = vendor_service.update_vendor(vendor_id, vendor_data, modified_by)
        return vendor
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating vendor: {str(e)}"
        )


@router.get("/{vendor_id}", response_model=VendorProfileDetailResponse)
def get_vendor(vendor_id: int, db: Session = Depends(get_db)):
    """
    Get vendor by ID with all related information.
    DSA-64: View Vendor Profile Details
    
    Includes:
    - Basic information at first glance
    - "More" section with additional details
    - Highlighting for overdue due diligence (red)
    - Color coding for status (Active=green, Inactive=black)
    """
    vendor_service = VendorService(db)
    
    # Use service method to get vendor with highlighting
    vendor_data = vendor_service.get_vendor_profile_with_details(vendor_id)
    
    if not vendor_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    
    # Return using Pydantic schema
    return vendor_data


@router.get("/vendor-id/{vendor_id}", response_model=VendorDetailResponse)
def get_vendor_by_vendor_id(vendor_id: str, db: Session = Depends(get_db)):
    """
    Get vendor by vendor ID (AB1, OB1, etc.) with all related information.
    """
    vendor_service = VendorService(db)
    vendor = vendor_service.get_vendor_by_vendor_id(vendor_id)
    
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    
    return vendor


@router.get("/", response_model=VendorListResponse)
def get_vendors(
    skip: int = 0,
    limit: int = 100,
    page_size: Optional[int] = None,
    status_filter: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get list of vendors with advanced search, filtering, and pagination.
    DSA-59: View Vendor List
    DSA-60: Search and Filter Vendors
    
    Supports:
    - Pagination with customizable page_size (10, 25, 50, 100)
    - Status filtering (All, Active, Inactive)
    - Search by vendor name, ID, contact person, email
    - Color coding for status (Active=green, Inactive=black)
    """
    from app.models.vendor import VendorStatusType
    from datetime import date
    
    # Use page_size if provided, otherwise use limit
    effective_limit = page_size if page_size else limit
    
    # Validate page_size
    if page_size and page_size not in [10, 25, 50, 100]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="page_size must be one of: 10, 25, 50, 100"
        )
    
    vendor_service = VendorService(db)
    
    # Use service method for filtering and search
    vendors, total_count = vendor_service.get_vendors_with_filters(
        skip=skip,
        limit=effective_limit,
        status_filter=status_filter,
        search=search
    )
    
    # Build response using Pydantic schema
    vendor_items = []
    for vendor in vendors:
        # Determine if due diligence is overdue
        is_overdue = False
        if vendor.next_required_due_diligence_date:
            is_overdue = vendor.next_required_due_diligence_date.date() < date.today()
        
        # Get primary email
        primary_email = next(
            (e.email for e in vendor.emails if e.is_primary),
            vendor.emails[0].email if vendor.emails else None
        )
        
        vendor_items.append(VendorListItemResponse(
            id=vendor.id,
            vendor_id=vendor.vendor_id,
            vendor_name=vendor.vendor_name,
            vendor_contact_person=vendor.vendor_contact_person,
            email=primary_email,
            next_required_due_diligence_date=vendor.next_required_due_diligence_date,
            status=vendor.status,
            status_color="green" if vendor.status == VendorStatusType.ACTIVE else "black",
            is_due_diligence_overdue=is_overdue
        ))
    
    # Return with pagination metadata using Pydantic schema
    return VendorListResponse(
        vendors=vendor_items,
        total_count=total_count,
        page=skip // effective_limit + 1 if effective_limit > 0 else 1,
        page_size=effective_limit,
        total_pages=(total_count + effective_limit - 1) // effective_limit if effective_limit > 0 else 1,
        has_results=len(vendor_items) > 0,
        message="No results found" if len(vendor_items) == 0 else None
    )


@router.post("/{vendor_id}/documents", response_model=VendorDocumentResponse)
async def upload_vendor_document(
    vendor_id: int,
    document_type: str = Form(..., description="Document type (e.g., 'Due Diligence', 'Non-Disclosure Agreement')"),
    custom_document_name: str = Form(..., description="Custom name for the document"),
    document_signed_date: str = Form(..., description="Document signed date (YYYY-MM-DD)"),
    file: UploadFile = File(..., description="Document file (PDF only)"),
    db: Session = Depends(get_db)
):
    """
    Upload a document for an existing vendor with custom name and signed date.
    """
    vendor_service = VendorService(db)
    
    try:
        # Convert string to DocumentType enum
        try:
            doc_type_enum = DocumentType(document_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid document type. Valid types: {[dt.value for dt in DocumentType]}"
            )
        
        from datetime import datetime
        signed_date = datetime.fromisoformat(document_signed_date)
        document = await vendor_service.upload_vendor_document(
            vendor_id, file, doc_type_enum, custom_document_name, signed_date
        )
        return document
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format. Use YYYY-MM-DD: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading document: {str(e)}"
        )


@router.get("/{vendor_id}/required-documents")
def get_required_documents(vendor_id: int, db: Session = Depends(get_db)):
    """
    Get list of required and optional documents for a vendor.
    """
    vendor_service = VendorService(db)
    vendor = vendor_service.get_vendor_by_id(vendor_id)
    
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    
    # Use direct methods to avoid creating VendorCreate with empty lists
    required_docs = vendor_service.get_required_documents_for_vendor_direct(
        vendor.due_diligence_required,
        vendor.material_outsourcing_arrangement
    )
    optional_docs = vendor_service.get_optional_documents_for_vendor_direct(
        vendor.due_diligence_required,
        vendor.material_outsourcing_arrangement
    )
    
    return {
        "vendor_id": vendor.vendor_id,
        "required_documents": [doc.value for doc in required_docs],
        "optional_documents": [doc.value for doc in optional_docs],
        "uploaded_documents": [doc.document_type.value for doc in vendor.documents]
    }


@router.get("/validation/countries")
def get_supported_countries():
    """
    Get list of supported countries with their validation rules.
    """
    return {
        "aruba_countries": ["Aruba", "Curacao", "Bonaire", "Saint Martin"],
        "validation_rules": {
            "aruba_countries": {
                "address": "required",
                "city": "hidden",
                "state": "hidden", 
                "zip_code": "hidden"
            },
            "other_countries": {
                "address": "required",
                "city": "optional",
                "state": "optional (dropdown for US)",
                "zip_code": "optional"
            }
        }
    }


@router.get("/validation/enums")
def get_validation_enums():
    """
    Get all enum values for form validation.
    """
    return {
        "bank_customer_types": ["Aruba Bank", "Orco Bank", "None"],
        "material_outsourcing_types": ["Yes", "No"],
        "due_diligence_required_types": ["Yes", "No"],
        "alert_frequency_types": ["15 days", "30 days", "60 days", "90 days", "120 days"],
        "document_types": [
            "Due Diligence",
            "Non-Disclosure Agreement", 
            "Integrity Policy",
            "Risk Assessment Form",
            "Business Continuity Plan",
            "Disaster Recovery Plan",
            "Insurance Policy"
        ]
    }


@router.get("/{vendor_id}/documents", response_model=VendorDocumentsResponse)
def get_vendor_documents(
    vendor_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all documents for a specific vendor, grouped by document type.
    DSA-62: View Additional Documents
    """
    vendor_service = VendorService(db)
    
    # Use service method to get documents grouped by type
    documents_data = vendor_service.get_vendor_documents_grouped(vendor_id)
    
    if not documents_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    
    # Return using Pydantic schema
    return documents_data


@router.get(
    "/{vendor_id}/documents/summary",
    response_model=VendorDocumentsSummaryResponse
)
def get_vendor_documents_summary(
    vendor_id: int,
    db: Session = Depends(get_db)
):
    """
    Get summary of documents for a vendor.
    DSA-65: Documents Section
    Shows count of Vendor Contracts and Supporting Documents.
    """
    vendor_service = VendorService(db)
    
    # Use service method to get documents summary
    summary_data = vendor_service.get_vendor_documents_summary(vendor_id)
    
    if not summary_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    
    # Return using Pydantic schema
    return summary_data


@router.put("/{vendor_id}/email", response_model=VendorEmailResponse)
def update_vendor_primary_email(
    vendor_id: int,
    email: str,
    db: Session = Depends(get_db)
):
    """
    Update the primary email for a vendor.
    """
    vendor_service = VendorService(db)
    
    try:
        updated_email = vendor_service.update_vendor_primary_email(vendor_id, email)
        return updated_email
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating vendor email: {str(e)}"
        )


@router.put("/{vendor_id}/phone", response_model=VendorPhoneResponse)
def update_vendor_primary_phone(
    vendor_id: int,
    area_code: str,
    phone_number: str,
    db: Session = Depends(get_db)
):
    """
    Update the primary phone for a vendor.
    """
    vendor_service = VendorService(db)
    
    try:
        updated_phone = vendor_service.update_vendor_primary_phone(vendor_id, area_code, phone_number)
        return updated_phone
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating vendor phone: {str(e)}"
        )


@router.put("/{vendor_id}/address", response_model=VendorAddressResponse)
def update_vendor_primary_address(
    vendor_id: int,
    address: str,
    city: Optional[str] = None,
    state: Optional[str] = None,
    zip_code: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Update the primary address for a vendor.
    """
    vendor_service = VendorService(db)
    
    try:
        updated_address = vendor_service.update_vendor_primary_address(
            vendor_id, address, city, state, zip_code
        )
        return updated_address
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating vendor address: {str(e)}"
        )


@router.get("/{vendor_id}/contracts")
def get_vendor_contracts(
    vendor_id: int,
    skip: int = 0,
    limit: int = 10,
    status_filter: Optional[str] = None,
    contract_type: Optional[str] = None,
    department: Optional[str] = None,
    owner_id: Optional[int] = None,
    search: Optional[str] = None,
    sort_by: Optional[str] = "end_date",
    sort_order: Optional[str] = "asc",
    db: Session = Depends(get_db)
):
    """
    Get all contracts for a specific vendor.
    Supports pagination, filtering, search, and sorting.
    """
    from app.models.contract import Contract, User
    from sqlalchemy import or_, desc, asc
    
    # Verify vendor exists
    vendor_service = VendorService(db)
    vendor = vendor_service.get_vendor_by_id(vendor_id)
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    
    # Base query
    query = db.query(Contract).filter(Contract.vendor_id == vendor_id)
    
    # Apply filters
    if status_filter:
        query = query.filter(Contract.status == status_filter)
    
    if contract_type:
        query = query.filter(Contract.contract_type == contract_type)
    
    if department:
        query = query.filter(Contract.department == department)
    
    if owner_id:
        query = query.filter(Contract.contract_owner_id == owner_id)
    
    # Apply search
    if search:
        search_filter = or_(
            Contract.contract_id.ilike(f"%{search}%"),
            Contract.contract_description.ilike(f"%{search}%"),
            Contract.contract_type.ilike(f"%{search}%"),
            Contract.department.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    # Apply sorting
    if sort_by and hasattr(Contract, sort_by):
        order_func = desc if sort_order == "desc" else asc
        query = query.order_by(order_func(getattr(Contract, sort_by)))
    
    # Apply pagination - MSSQL requires ORDER BY when using OFFSET
    contracts = query.order_by(Contract.id).offset(skip).limit(limit).all()
    
    # Format response
    result = []
    for contract in contracts:
        owner = db.query(User).filter(
            User.id == contract.contract_owner_id
        ).first()
        result.append({
            "id": contract.id,
            "contract_id": contract.contract_id,
            "vendor_name": vendor.vendor_name,
            "type": contract.contract_type.value if hasattr(contract.contract_type, 'value') else contract.contract_type,
            "description": contract.contract_description,
            "department": contract.department.value if hasattr(contract.department, 'value') else contract.department,
            "owner": f"{owner.first_name} {owner.last_name}" if owner else "Unknown",
            "start_date": contract.start_date.isoformat(),
            "end_date": contract.end_date.isoformat(),
            "status": contract.status.value if hasattr(contract.status, 'value') else contract.status,
            "contract_amount": float(contract.contract_amount),
            "contract_currency": contract.contract_currency.value if hasattr(contract.contract_currency, 'value') else contract.contract_currency
        })
    
    return result