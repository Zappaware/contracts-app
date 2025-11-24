from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import json
from pydantic import ValidationError

from app.db.database import get_db
from app.services.vendor_service import VendorService
from app.schemas.vendor import (
    VendorCreate, VendorResponse, VendorDetailResponse,
    DocumentType, VendorDocumentResponse
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
        vendor_dict = json.loads(vendor_data)
        vendor_create = VendorCreate(**vendor_dict)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON format in vendor_data"
        )
    except ValidationError as e:
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
        
        # Create vendor
        vendor = vendor_service.create_vendor(vendor_create, bank_type)
        
        # Upload documents with custom names and signed dates
        uploaded_docs = []
        
        if due_diligence_doc:
            from datetime import datetime
            signed_date = datetime.fromisoformat(due_diligence_signed_date)
            doc = await vendor_service.upload_vendor_document(
                vendor.id, due_diligence_doc, DocumentType.DUE_DILIGENCE,
                due_diligence_name, signed_date
            )
            uploaded_docs.append(doc)
        
        if non_disclosure_doc:
            signed_date = datetime.fromisoformat(non_disclosure_signed_date)
            doc = await vendor_service.upload_vendor_document(
                vendor.id, non_disclosure_doc, DocumentType.NON_DISCLOSURE_AGREEMENT,
                non_disclosure_name, signed_date
            )
            uploaded_docs.append(doc)
        
        if integrity_policy_doc:
            signed_date = datetime.fromisoformat(integrity_policy_signed_date)
            doc = await vendor_service.upload_vendor_document(
                vendor.id, integrity_policy_doc, DocumentType.INTEGRITY_POLICY,
                integrity_policy_name, signed_date
            )
            uploaded_docs.append(doc)
        
        if risk_assessment_doc:
            signed_date = datetime.fromisoformat(risk_assessment_signed_date)
            doc = await vendor_service.upload_vendor_document(
                vendor.id, risk_assessment_doc, DocumentType.RISK_ASSESSMENT_FORM,
                risk_assessment_name, signed_date
            )
            uploaded_docs.append(doc)
        
        if business_continuity_doc:
            signed_date = datetime.fromisoformat(business_continuity_signed_date)
            doc = await vendor_service.upload_vendor_document(
                vendor.id, business_continuity_doc, DocumentType.BUSINESS_CONTINUITY_PLAN,
                business_continuity_name, signed_date
            )
            uploaded_docs.append(doc)
        
        if disaster_recovery_doc:
            signed_date = datetime.fromisoformat(disaster_recovery_signed_date)
            doc = await vendor_service.upload_vendor_document(
                vendor.id, disaster_recovery_doc, DocumentType.DISASTER_RECOVERY_PLAN,
                disaster_recovery_name, signed_date
            )
            uploaded_docs.append(doc)
        
        if insurance_policy_doc:
            signed_date = datetime.fromisoformat(insurance_policy_signed_date)
            doc = await vendor_service.upload_vendor_document(
                vendor.id, insurance_policy_doc, DocumentType.INSURANCE_POLICY,
                insurance_policy_name, signed_date
            )
            uploaded_docs.append(doc)
        
        # Refresh vendor to get all related data
        db.refresh(vendor)
        
        return vendor
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating vendor: {str(e)}"
        )


@router.get("/{vendor_id}", response_model=VendorDetailResponse)
def get_vendor(vendor_id: int, db: Session = Depends(get_db)):
    """
    Get vendor by ID with all related information.
    """
    vendor_service = VendorService(db)
    vendor = vendor_service.get_vendor_by_id(vendor_id)
    
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    
    return vendor


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


@router.get("/", response_model=List[VendorResponse])
def get_vendors(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """
    Get list of vendors with pagination.
    """
    vendor_service = VendorService(db)
    vendors = vendor_service.get_vendors(skip=skip, limit=limit)
    return vendors


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