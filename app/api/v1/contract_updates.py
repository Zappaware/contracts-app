from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime, date, timedelta
from pydantic import BaseModel

from app.db.database import get_db
from app.models.contract import Contract, ContractUpdate, ContractUpdateStatus, User
from app.models.vendor import Vendor

router = APIRouter()


class ContractUpdateResponse(BaseModel):
    id: int
    contract_id: str
    contract_db_id: int  # Database ID for linking to contract-info page
    vendor_name: str
    vendor_id: Optional[int]
    contract_type: str
    description: str
    expiration_date: date
    manager: str
    role: str
    response_provided_by: Optional[str]
    response_date: Optional[datetime]
    has_document: bool
    status: str
    admin_comments: Optional[str]
    returned_reason: Optional[str]
    returned_date: Optional[datetime]
    correction_date: Optional[datetime]
    initial_vendor_name: Optional[str]
    initial_contract_type: Optional[str]
    initial_description: Optional[str]
    initial_expiration_date: Optional[date]
    previous_update_id: Optional[int]
    decision: Optional[str] = None
    decision_comments: Optional[str] = None
    
    class Config:
        from_attributes = True


class ContractUpdateCreate(BaseModel):
    contract_id: int
    status: str
    response_provided_by_user_id: Optional[int] = None
    has_document: bool = False
    admin_comments: Optional[str] = None
    returned_reason: Optional[str] = None
    initial_vendor_name: Optional[str] = None
    initial_contract_type: Optional[str] = None
    initial_description: Optional[str] = None
    initial_expiration_date: Optional[date] = None
    decision: Optional[str] = None
    decision_comments: Optional[str] = None


class ContractUpdatePatch(BaseModel):
    status: Optional[str] = None
    admin_comments: Optional[str] = None
    returned_reason: Optional[str] = None
    initial_vendor_name: Optional[str] = None
    initial_contract_type: Optional[str] = None
    initial_description: Optional[str] = None
    initial_expiration_date: Optional[date] = None
    decision: Optional[str] = None
    decision_comments: Optional[str] = None


def _fetch_contract_updates(
    db: Session,
    status: Optional[str] = None,
    owner_id: Optional[int] = None,
) -> List[ContractUpdateResponse]:
    """Internal helper: fetch contract updates with plain defaults (callable from other endpoints)."""
    query = db.query(ContractUpdate).options(
        joinedload(ContractUpdate.contract).joinedload(Contract.vendor),
        joinedload(ContractUpdate.contract).joinedload(Contract.contract_owner),
        joinedload(ContractUpdate.response_provided_by)
    ).join(Contract)
    
    if status:
        query = query.filter(ContractUpdate.status == status)
    
    if owner_id:
        query = query.filter(Contract.contract_owner_id == owner_id)
    
    updates = query.order_by(ContractUpdate.created_at.desc()).all()
    
    result = []
    for update in updates:
        contract = update.contract
        vendor = contract.vendor
        
        # Determine manager name and role
        manager_name = f"{contract.contract_owner.first_name} {contract.contract_owner.last_name}"
        
        # Determine who provided the response (already loaded via joinedload)
        response_provided_by = None
        role = "owned"
        if update.response_provided_by:
            response_provided_by = f"{update.response_provided_by.first_name} {update.response_provided_by.last_name}"
            # Determine if it's owner or backup
            if contract.contract_owner_id == update.response_provided_by_user_id:
                role = "owned"
            elif contract.contract_owner_backup_id == update.response_provided_by_user_id:
                role = "backup"
        
        result.append(ContractUpdateResponse(
            id=update.id,
            contract_id=contract.contract_id,
            contract_db_id=contract.id,  # Database ID for linking
            vendor_name=vendor.vendor_name,
            vendor_id=vendor.id,
            contract_type=contract.contract_type.value,
            description=contract.contract_description,
            expiration_date=contract.end_date,
            manager=manager_name,
            role=role,
            response_provided_by=response_provided_by,
            response_date=update.response_date,
            has_document=update.has_document,
            status=update.status.value,
            admin_comments=update.admin_comments,
            returned_reason=update.returned_reason,
            returned_date=update.returned_date,
            correction_date=update.correction_date,
            initial_vendor_name=update.initial_vendor_name,
            initial_contract_type=update.initial_contract_type,
            initial_description=update.initial_description,
            initial_expiration_date=update.initial_expiration_date,
            previous_update_id=update.previous_update_id,
        decision=update.decision,
        decision_comments=update.decision_comments,
    ))
    
    return result


@router.get("/", response_model=List[ContractUpdateResponse])
def get_contract_updates(
    status: Optional[str] = Query(None, description="Filter by status (returned, updated, pending_review, completed)"),
    owner_id: Optional[int] = Query(None, description="Filter by contract owner ID"),
    db: Session = Depends(get_db)
):
    """Get all contract updates, optionally filtered by status and owner"""
    return _fetch_contract_updates(db=db, status=status, owner_id=owner_id)


@router.get("/returned", response_model=List[ContractUpdateResponse])
def get_returned_contracts(
    owner_id: Optional[int] = Query(None, description="Filter by contract owner ID"),
    db: Session = Depends(get_db)
):
    """Get all returned contracts (for Contract Manager dashboard)"""
    return get_contract_updates(status="returned", owner_id=owner_id, db=db)


@router.post("/", response_model=ContractUpdateResponse, status_code=status.HTTP_201_CREATED)
def create_contract_update(
    update_data: ContractUpdateCreate,
    db: Session = Depends(get_db)
):
    """Create a new contract update/review entry"""
    # Verify contract exists
    contract = db.query(Contract).filter(Contract.id == update_data.contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    # Create update
    contract_update = ContractUpdate(
        contract_id=update_data.contract_id,
        status=ContractUpdateStatus(update_data.status),
        response_provided_by_user_id=update_data.response_provided_by_user_id,
        response_date=datetime.utcnow() if update_data.response_provided_by_user_id else None,
        has_document=update_data.has_document,
        admin_comments=update_data.admin_comments,
        returned_reason=update_data.returned_reason,
        returned_date=datetime.utcnow() if update_data.status == "returned" else None,
        initial_vendor_name=update_data.initial_vendor_name,
        initial_contract_type=update_data.initial_contract_type,
        initial_description=update_data.initial_description,
        initial_expiration_date=update_data.initial_expiration_date,
        decision=update_data.decision,
        decision_comments=update_data.decision_comments,
    )
    
    db.add(contract_update)
    db.commit()
    db.refresh(contract_update)
    
    # Return response - use _fetch_contract_updates (not get_contract_updates) to avoid Query() default in internal calls
    updates = _fetch_contract_updates(db=db, status=update_data.status)
    return updates[0] if updates else None


@router.patch("/{update_id}", response_model=ContractUpdateResponse)
def update_contract_update(
    update_id: int,
    update_data: ContractUpdatePatch,
    db: Session = Depends(get_db)
):
    """Update a contract update entry (e.g., change status, add comments)"""
    contract_update = db.query(ContractUpdate).filter(ContractUpdate.id == update_id).first()
    if not contract_update:
        raise HTTPException(status_code=404, detail="Contract update not found")
    
    # Update fields
    if update_data.status:
        contract_update.status = ContractUpdateStatus(update_data.status)
        if update_data.status == "returned" and not contract_update.returned_date:
            contract_update.returned_date = datetime.utcnow()
        elif update_data.status == "updated" and not contract_update.correction_date:
            contract_update.correction_date = datetime.utcnow()
    
    if update_data.admin_comments is not None:
        contract_update.admin_comments = update_data.admin_comments
    
    if update_data.returned_reason is not None:
        contract_update.returned_reason = update_data.returned_reason
    
    if update_data.initial_vendor_name is not None:
        contract_update.initial_vendor_name = update_data.initial_vendor_name
    
    if update_data.initial_contract_type is not None:
        contract_update.initial_contract_type = update_data.initial_contract_type
    
    if update_data.initial_description is not None:
        contract_update.initial_description = update_data.initial_description
    
    if update_data.initial_expiration_date is not None:
        contract_update.initial_expiration_date = update_data.initial_expiration_date

    if update_data.decision is not None:
        contract_update.decision = update_data.decision

    if update_data.decision_comments is not None:
        contract_update.decision_comments = update_data.decision_comments
    
    contract_update.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(contract_update)
    
    # Return updated response - use _fetch_contract_updates to avoid Query() default in internal calls
    updates = _fetch_contract_updates(db=db)
    for update in updates:
        if update.id == update_id:
            return update
    
    raise HTTPException(status_code=500, detail="Error retrieving updated contract update")


@router.delete("/{update_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contract_update(
    update_id: int,
    db: Session = Depends(get_db)
):
    """Delete a contract update entry (used when processing/completing)"""
    contract_update = db.query(ContractUpdate).filter(ContractUpdate.id == update_id).first()
    if not contract_update:
        raise HTTPException(status_code=404, detail="Contract update not found")
    
    db.delete(contract_update)
    db.commit()
    
    return None

