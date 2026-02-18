from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import json
from datetime import datetime
from pydantic import ValidationError

from app.db.database import get_db
from app.services.contract_service import ContractService
from app.schemas.contract import (
    ContractCreate, ContractUpdate, ContractDetailResponse,
    ContractListResponse, ContractSearchResponse,
    UserCreate, UserResponse, UserListResponse, ContractValidationEnums,
    ContractSummary, ContractDocumentResponse,
    TerminationDocumentResponse, TerminationDocumentUpdate,
    TerminationDocumentFromContractDocument,
)
from app.models.contract import (
    ContractType, DepartmentType, NoticePeriodType, ExpirationNoticePeriodType,
    CurrencyType, PaymentMethodType, RenewalPeriodType, User, ContractStatusType
)

router = APIRouter()


@router.post("/", response_model=ContractDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_contract(
    contract_data: str = Form(..., description="JSON string of contract data"),
    contract_document: UploadFile = File(..., description="Contract document (PDF only)"),
    document_name: str = Form(..., description="Custom name for the contract document"),
    document_signed_date: str = Form(..., description="Document signed date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    Create a new contract with all required information and document.
    
    The contract_data should be a JSON string containing all contract information.
    The contract document is uploaded as a PDF file with custom name and signed date.
    """
    try:
        # Parse contract data from JSON string
        contract_dict = json.loads(contract_data)
        contract_create = ContractCreate(**contract_dict)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON format in contract_data"
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {e}"
        )
    
    contract_service = ContractService(db)
    
    # Validate contract creation requirements
    validation_errors = contract_service.validate_contract_creation_requirements(contract_create)
    if validation_errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"errors": validation_errors}
        )
    
    try:
        # Parse document signed date
        signed_date = datetime.fromisoformat(document_signed_date).date()
        
        # Create contract
        contract = contract_service.create_contract(contract_create)
        
        # Upload contract document
        await contract_service.upload_contract_document(
            contract.id, contract_document, document_name, signed_date
        )
        
        # Refresh contract to get all related data
        db.refresh(contract)
        
        # Build response with vendor as dict
        response_data = {
            **{k: v for k, v in contract.__dict__.items() if not k.startswith('_')},
            "vendor": {
                "id": contract.vendor.id,
                "vendor_id": contract.vendor.vendor_id,
                "vendor_name": contract.vendor.vendor_name,
                "vendor_country": contract.vendor.vendor_country
            },
            "contract_owner": contract.contract_owner,
            "contract_owner_backup": contract.contract_owner_backup,
            "contract_owner_manager": contract.contract_owner_manager,
            "documents": contract.documents
        }
        
        return response_data
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format. Use YYYY-MM-DD: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating contract: {str(e)}"
        )


@router.put("/{contract_id}", response_model=ContractDetailResponse)
def update_contract(
    contract_id: int,
    contract_data: ContractUpdate,
    modified_by: str = "SYSTEM",
    db: Session = Depends(get_db)
):
    """
    Update existing contract with audit trail.
    The modified_by parameter can be passed as a query parameter.
    """
    contract_service = ContractService(db)
    
    try:
        contract = contract_service.update_contract(contract_id, contract_data, modified_by)
        
        # Build response with vendor as dict
        response_data = {
            **{k: v for k, v in contract.__dict__.items() if not k.startswith('_')},
            "vendor": {
                "id": contract.vendor.id,
                "vendor_id": contract.vendor.vendor_id,
                "vendor_name": contract.vendor.vendor_name,
                "vendor_country": contract.vendor.vendor_country
            },
            "contract_owner": contract.contract_owner,
            "contract_owner_backup": contract.contract_owner_backup,
            "contract_owner_manager": contract.contract_owner_manager,
            "documents": contract.documents
        }
        
        return response_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating contract: {str(e)}"
        )


@router.get("/{contract_id}", response_model=ContractDetailResponse)
def get_contract(contract_id: int, db: Session = Depends(get_db)):
    """
    Get contract by ID with all related information.
    """
    contract_service = ContractService(db)
    contract = contract_service.get_contract_by_id(contract_id)
    
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found"
        )
    
    # Build response with vendor as dict
    response_data = {
        **{k: v for k, v in contract.__dict__.items() if not k.startswith('_')},
        "vendor": {
            "id": contract.vendor.id,
            "vendor_id": contract.vendor.vendor_id,
            "vendor_name": contract.vendor.vendor_name,
            "vendor_country": contract.vendor.vendor_country
        },
        "contract_owner": contract.contract_owner,
        "contract_owner_backup": contract.contract_owner_backup,
        "contract_owner_manager": contract.contract_owner_manager,
        "documents": contract.documents
    }
    
    return response_data


@router.get("/contract-id/{contract_id}", response_model=ContractDetailResponse)
def get_contract_by_contract_id(contract_id: str, db: Session = Depends(get_db)):
    """
    Get contract by contract ID (CT1, CT2, etc.) with all related information.
    """
    contract_service = ContractService(db)
    contract = contract_service.get_contract_by_contract_id(contract_id)
    
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found"
        )
    
    # Build response with vendor as dict
    response_data = {
        **{k: v for k, v in contract.__dict__.items() if not k.startswith('_')},
        "vendor": {
            "id": contract.vendor.id,
            "vendor_id": contract.vendor.vendor_id,
            "vendor_name": contract.vendor.vendor_name,
            "vendor_country": contract.vendor.vendor_country
        },
        "contract_owner": contract.contract_owner,
        "contract_owner_backup": contract.contract_owner_backup,
        "contract_owner_manager": contract.contract_owner_manager,
        "documents": contract.documents
    }
    
    return response_data


@router.get("/", response_model=ContractSearchResponse)
def get_contracts(
    skip: int = Query(0, ge=0, description="Number of contracts to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max contracts per page"),
    search: Optional[str] = Query(None, description="Search keyword"),
    status: Optional[ContractStatusType] = Query(None, description="Filter by status"),
    contract_type: Optional[ContractType] = Query(None, description="Filter by type"),
    department: Optional[DepartmentType] = Query(None, description="Filter by department"),
    owner_id: Optional[int] = Query(None, description="Filter by contract owner ID"),
    vendor_id: Optional[int] = Query(None, description="Filter by vendor ID"),
    expiring_soon: Optional[bool] = Query(None, description="Filter expiring within 30 days"),
    db: Session = Depends(get_db)
):
    """
    Advanced search and filter contracts with pagination.
    
    DSA-42: Supports keyword search, combined filters, and pagination.
    Returns contracts list with total count for pagination UI.
    """
    contract_service = ContractService(db)
    
    # Use advanced search and filter
    contracts, total_count = contract_service.search_and_filter_contracts(
        skip=skip,
        limit=limit,
        search=search,
        status=status,
        contract_type=contract_type.value if contract_type else None,
        department=department.value if department else None,
        owner_id=owner_id,
        vendor_id=vendor_id,
        expiring_soon=expiring_soon
    )
    
    # Convert to list response format
    contract_list = []
    for contract in contracts:
        contract_list.append({
            "id": contract.id,
            "contract_id": contract.contract_id,
            "vendor_name": contract.vendor.vendor_name,
            "contract_description": contract.contract_description,
            "contract_type": contract.contract_type,
            "start_date": contract.start_date,
            "end_date": contract.end_date,
            "contract_amount": contract.contract_amount,
            "contract_currency": contract.contract_currency,
            "department": contract.department,
            "status": contract.status,
            "contract_owner_name": f"{contract.contract_owner.first_name} {contract.contract_owner.last_name}",
            "created_at": contract.created_at
        })
    
    return {
        "contracts": contract_list,
        "total_count": total_count,
        "page": skip // limit + 1 if limit > 0 else 1,
        "page_size": limit,
        "total_pages": (total_count + limit - 1) // limit if limit > 0 else 1
    }


@router.post("/{contract_id}/documents", response_model=ContractDocumentResponse)
async def upload_contract_document(
    contract_id: int,
    document_name: str = Form(..., description="Custom name for the document"),
    document_signed_date: str = Form(..., description="Document signed date (YYYY-MM-DD)"),
    file: UploadFile = File(..., description="Document file (PDF only)"),
    db: Session = Depends(get_db)
):
    """
    Upload an additional document for an existing contract.
    """
    contract_service = ContractService(db)
    
    try:
        signed_date = datetime.fromisoformat(document_signed_date).date()
        document = await contract_service.upload_contract_document(
            contract_id, file, document_name, signed_date
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


# --- Termination documents ---
@router.get("/{contract_id}/termination-documents", response_model=List[TerminationDocumentResponse])
def list_termination_documents(contract_id: int, db: Session = Depends(get_db)):
    """List all termination documents for a contract. All roles can view."""
    contract_service = ContractService(db)
    contract = contract_service.get_contract_by_id(contract_id)
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    # Load termination_documents if not loaded
    from sqlalchemy.orm import joinedload
    from app.models.contract import Contract as ContractModel
    contract = db.query(ContractModel).options(joinedload(ContractModel.termination_documents)).filter(ContractModel.id == contract_id).first()
    return contract.termination_documents or []


@router.post("/{contract_id}/termination-documents", response_model=TerminationDocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_termination_document(
    contract_id: int,
    document_name: str = Form(..., description="Document display name"),
    document_date: str = Form(..., description="Document date (YYYY-MM-DD)"),
    file: UploadFile = File(..., description="PDF file"),
    db: Session = Depends(get_db)
):
    """Upload a termination document. Contract Admin and Super User only (enforced in UI)."""
    contract_service = ContractService(db)
    try:
        doc_date = datetime.fromisoformat(document_date).date()
        doc = await contract_service.upload_termination_document(contract_id, file, document_name, doc_date)
        return doc
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post(
    "/{contract_id}/termination-documents/from-contract-document",
    response_model=TerminationDocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_termination_document_from_contract_document(
    contract_id: int,
    body: TerminationDocumentFromContractDocument,
    db: Session = Depends(get_db),
):
    """
    Create a termination document by copying an existing contract document
    (e.g. when Contract Admin completes review with decision Terminate).
    """
    contract_service = ContractService(db)
    try:
        doc = contract_service.add_termination_document_from_contract_document(
            contract_id,
            body.contract_document_id,
            body.document_date,
        )
        return doc
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{contract_id}/termination-documents/{doc_id}", response_model=TerminationDocumentResponse)
def get_termination_document(contract_id: int, doc_id: int, db: Session = Depends(get_db)):
    """Get one termination document. All roles can view."""
    contract_service = ContractService(db)
    doc = contract_service.get_termination_document(contract_id, doc_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Termination document not found")
    return doc


@router.put("/{contract_id}/termination-documents/{doc_id}", response_model=TerminationDocumentResponse)
def update_termination_document(
    contract_id: int,
    doc_id: int,
    body: TerminationDocumentUpdate,
    db: Session = Depends(get_db)
):
    """Update termination document name/date. Contract Admin and Super User only (enforced in UI)."""
    contract_service = ContractService(db)
    try:
        doc = contract_service.update_termination_document(
            contract_id, doc_id,
            document_name=body.document_name,
            document_date=body.document_date
        )
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Termination document not found")
        return doc
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{contract_id}/termination-documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_termination_document(contract_id: int, doc_id: int, db: Session = Depends(get_db)):
    """Delete a termination document. Contract Admin and Super User only (enforced in UI)."""
    contract_service = ContractService(db)
    ok = contract_service.delete_termination_document(contract_id, doc_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Termination document not found")


@router.get("/{contract_id}/termination-documents/{doc_id}/download")
def download_termination_document(contract_id: int, doc_id: int, db: Session = Depends(get_db)):
    """Download termination document file. All roles can download."""
    from fastapi.responses import FileResponse
    contract_service = ContractService(db)
    doc = contract_service.get_termination_document(contract_id, doc_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Termination document not found")
    import os
    if not os.path.exists(doc.file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return FileResponse(doc.file_path, filename=doc.file_name, media_type=doc.content_type or "application/pdf")


@router.get("/summary/dashboard", response_model=ContractSummary)
def get_contract_summary(db: Session = Depends(get_db)):
    """
    Get contract summary statistics for dashboard.
    """
    contract_service = ContractService(db)
    return contract_service.get_contract_summary()


# User Management Endpoints
@router.post("/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user for contract ownership.
    """
    contract_service = ContractService(db)
    
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    try:
        user = contract_service.create_user(user_data)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}"
        )


@router.get("/users/", response_model=List[UserListResponse])
def get_users(
    active_only: bool = Query(True, description="Return only active users"),
    db: Session = Depends(get_db)
):
    """
    Get list of users for contract ownership selection.
    """
    contract_service = ContractService(db)
    users = contract_service.get_users(active_only=active_only)
    return users


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """
    Get user by ID with email information for display.
    """
    contract_service = ContractService(db)
    user = contract_service.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.get("/users/{user_id}/email")
def get_user_email(user_id: int, db: Session = Depends(get_db)):
    """
    Get user email for display when user is selected in dropdown.
    This endpoint supports the requirement to show email in read-only format.
    """
    contract_service = ContractService(db)
    user = contract_service.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "user_id": user.user_id,
        "email": user.email,
        "full_name": f"{user.first_name} {user.last_name}"
    }


# Validation and Helper Endpoints
@router.get("/validation/enums", response_model=ContractValidationEnums)
def get_validation_enums():
    """
    Get all enum values for form validation.
    """
    return ContractValidationEnums()


@router.get("/validation/vendors")
def get_vendors_for_dropdown(db: Session = Depends(get_db)):
    """
    Get list of vendors for dropdown selection.
    """
    from app.services.vendor_service import VendorService
    vendor_service = VendorService(db)
    vendors = vendor_service.get_vendors(skip=0, limit=1000)
    
    return [
        {
            "id": vendor.id,
            "vendor_id": vendor.vendor_id,
            "vendor_name": vendor.vendor_name,
            "vendor_country": vendor.vendor_country
        }
        for vendor in vendors
    ]


@router.get("/validation/departments")
def get_departments():
    """
    Get list of departments for dropdown selection.
    """
    return [
        {"value": dept.value, "label": dept.value}
        for dept in DepartmentType
    ]


@router.get("/validation/contract-types")
def get_contract_types():
    """
    Get list of contract types for dropdown selection.
    """
    return [
        {"value": ct.value, "label": ct.value}
        for ct in ContractType
    ]


@router.get("/validation/currencies")
def get_currencies():
    """
    Get list of currencies for dropdown selection.
    """
    return [
        {"value": curr.value, "label": curr.value}
        for curr in CurrencyType
    ]


@router.get("/validation/payment-methods")
def get_payment_methods():
    """
    Get list of payment methods for dropdown selection.
    """
    return [
        {"value": pm.value, "label": pm.value}
        for pm in PaymentMethodType
    ]


@router.get("/validation/notice-periods")
def get_notice_periods():
    """
    Get list of notice periods for dropdown selection.
    """
    return [
        {"value": np.value, "label": np.value}
        for np in NoticePeriodType
    ]


@router.get("/validation/renewal-periods")
def get_renewal_periods():
    """
    Get list of renewal periods for dropdown selection.
    """
    return [
        {"value": rp.value, "label": rp.value}
        for rp in RenewalPeriodType
    ]


@router.get("/validation/expiration-notice-periods")
def get_expiration_notice_periods():
    """
    Get list of expiration notice periods for dropdown selection.
    """
    return [
        {"value": enp.value, "label": enp.value}
        for enp in ExpirationNoticePeriodType
    ]


@router.post("/{contract_id}/save-pending-termination")
def save_pending_termination(
    contract_id: int,
    termination_decision: str = Form(...),
    termination_date: Optional[str] = Form(None),
    modified_by: str = Form("SYSTEM"),
    db: Session = Depends(get_db)
):
    """
    Save termination decision without uploading documents.
    Marks contract as 'Termination Pending – Documents Required'.
    """
    from datetime import datetime
    
    contract_service = ContractService(db)
    contract = contract_service.get_contract_by_id(contract_id)
    
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found"
        )
    
    if termination_decision not in ["Yes", "No"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Termination decision must be 'Yes' or 'No'"
        )
    
    if termination_decision == "Yes":
        if not termination_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Termination date required when decision is Yes"
            )
        
        term_date = datetime.fromisoformat(termination_date).date()
        contract.contract_termination = "Yes"
        contract.termination_date = term_date
        contract.status = "Termination Pending – Documents Required"
        contract.last_modified_by = modified_by
        contract.last_modified_date = datetime.now()
        
        db.commit()
        
        return {
            "message": "Termination saved. Upload required documents.",
            "contract_id": contract.contract_id,
            "status": contract.status,
            "pending_documents": ["Termination Letter", "Final Invoice"]
        }
    else:
        contract.contract_termination = "No"
        contract.last_modified_by = modified_by
        contract.last_modified_date = datetime.now()
        db.commit()
        
        return {
            "message": "Contract will remain active",
            "contract_id": contract.contract_id,
            "status": contract.status
        }


@router.post("/{contract_id}/extend")
def extend_contract(
    contract_id: int,
    new_end_date: str = Form(...),
    modified_by: str = Form("SYSTEM"),
    db: Session = Depends(get_db)
):
    """
    Extend contract by updating end date.
    """
    from datetime import datetime
    
    contract_service = ContractService(db)
    contract = contract_service.get_contract_by_id(contract_id)
    
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found"
        )
    
    end_date = datetime.fromisoformat(new_end_date).date()
    
    if end_date <= contract.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New end date must be after current end date"
        )
    
    contract.end_date = end_date
    contract.last_modified_by = modified_by
    contract.last_modified_date = datetime.now()
    
    db.commit()
    
    return {
        "message": "Contract extended successfully",
        "contract_id": contract.contract_id,
        "new_end_date": contract.end_date.isoformat(),
        "status": contract.status
    }


@router.post("/{contract_id}/terminate")
async def terminate_contract(
    contract_id: int,
    termination_date: str = Form(...),
    termination_letter: UploadFile = File(...),
    final_invoice: UploadFile = File(...),
    modified_by: str = Form("SYSTEM"),
    db: Session = Depends(get_db)
):
    """
    Terminate contract with required documents.
    """
    from datetime import datetime
    
    contract_service = ContractService(db)
    contract = contract_service.get_contract_by_id(contract_id)
    
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found"
        )
    
    if termination_letter.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Termination letter must be PDF"
        )
    
    if final_invoice.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Final invoice must be PDF"
        )
    
    term_date = datetime.fromisoformat(termination_date).date()
    
    # Save documents (simplified - adjust path as needed)
    import os
    upload_dir = "uploads/contracts"
    os.makedirs(upload_dir, exist_ok=True)
    
    letter_path = f"{upload_dir}/{contract.contract_id}_termination_letter.pdf"
    invoice_path = f"{upload_dir}/{contract.contract_id}_final_invoice.pdf"
    
    with open(letter_path, "wb") as f:
        f.write(await termination_letter.read())
    
    with open(invoice_path, "wb") as f:
        f.write(await final_invoice.read())
    
    contract.contract_termination = "Yes"
    contract.termination_date = term_date
    contract.termination_letter_path = letter_path
    contract.final_invoice_path = invoice_path
    contract.status = "Terminated"
    contract.last_modified_by = modified_by
    contract.last_modified_date = datetime.now()
    
    db.commit()
    
    return {
        "message": "Contract terminated successfully",
        "contract_id": contract.contract_id,
        "termination_date": contract.termination_date.isoformat(),
        "status": contract.status
    }