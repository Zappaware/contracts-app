"""
Dashboard endpoints for Contract Manager and Contract Admin
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date, timedelta

from app.db.database import get_db
from app.core.security import (
    get_current_active_user,
    require_contract_admin,
    require_contract_manager
)
from app.models.contract import User, UserRole
from app.services.contract_service import ContractService
from app.schemas.dashboard import (
    ContractManagerDashboard,
    ContractAdminDashboard,
    PendingDocumentsWorkbasket,
    ContractActionRequest,
    ContractActionResponse,
    ContractSummaryItem
)

router = APIRouter()


@router.get("/manager", response_model=ContractManagerDashboard)
def get_manager_dashboard(
    current_user: User = Depends(require_contract_manager),
    db: Session = Depends(get_db)
):
    """
    Get Contract Manager Dashboard (DSA-90, DSA-91)
    Shows contracts owned by the current manager
    """
    contract_service = ContractService(db)
    dashboard_data = contract_service.get_manager_dashboard_data(current_user.id)
    
    # Build contract summary items
    def build_summary_item(contract):
        today = date.today()
        days_until_exp = (contract.end_date - today).days if contract.end_date >= today else None
        
        return ContractSummaryItem(
            id=contract.id,
            contract_id=contract.contract_id,
            vendor_name=contract.vendor.vendor_name,
            contract_description=contract.contract_description,
            contract_type=contract.contract_type,
            start_date=contract.start_date,
            end_date=contract.end_date,
            status=contract.status,
            contract_amount=contract.contract_amount,
            contract_currency=contract.contract_currency,
            department=contract.department,
            contract_owner_name=f"{contract.contract_owner.first_name} {contract.contract_owner.last_name}",
            days_until_expiration=days_until_exp
        )
    
    expiring_contracts = [
        build_summary_item(c) for c in dashboard_data["expiring_contracts"]
    ]
    
    owned_contracts = [
        build_summary_item(c) for c in dashboard_data["owned_contracts"]
    ]
    
    return ContractManagerDashboard(
        user_id=current_user.id,
        user_name=f"{current_user.first_name} {current_user.last_name}",
        role=current_user.role.value if current_user.role else "Unknown",
        total_owned_contracts=dashboard_data["total_owned_contracts"],
        active_contracts=dashboard_data["active_contracts"],
        expiring_soon_contracts=dashboard_data["expiring_soon_contracts"],
        expired_contracts=dashboard_data["expired_contracts"],
        expiring_contracts=expiring_contracts,
        owned_contracts=owned_contracts
    )


@router.get("/admin", response_model=ContractAdminDashboard)
def get_admin_dashboard(
    current_user: User = Depends(require_contract_admin),
    db: Session = Depends(get_db)
):
    """
    Get Contract Admin Dashboard (DSA-96)
    Shows overview of all contracts in the system
    """
    contract_service = ContractService(db)
    dashboard_data = contract_service.get_admin_dashboard_data()
    
    # Build contract summary items
    def build_summary_item(contract):
        today = date.today()
        days_until_exp = (contract.end_date - today).days if contract.end_date >= today else None
        
        return ContractSummaryItem(
            id=contract.id,
            contract_id=contract.contract_id,
            vendor_name=contract.vendor.vendor_name,
            contract_description=contract.contract_description,
            contract_type=contract.contract_type,
            start_date=contract.start_date,
            end_date=contract.end_date,
            status=contract.status,
            contract_amount=contract.contract_amount,
            contract_currency=contract.contract_currency,
            department=contract.department,
            contract_owner_name=f"{contract.contract_owner.first_name} {contract.contract_owner.last_name}",
            days_until_expiration=days_until_exp
        )
    
    recent_contracts = [
        build_summary_item(c) for c in dashboard_data["recent_contracts"]
    ]
    
    expiring_soon = [
        build_summary_item(c) for c in dashboard_data["expiring_soon"]
    ]
    
    return ContractAdminDashboard(
        total_contracts=dashboard_data["total_contracts"],
        active_contracts=dashboard_data["active_contracts"],
        expired_contracts=dashboard_data["expired_contracts"],
        terminated_contracts=dashboard_data["terminated_contracts"],
        expiring_within_30_days=dashboard_data["expiring_within_30_days"],
        expiring_within_60_days=dashboard_data["expiring_within_60_days"],
        expiring_within_90_days=dashboard_data["expiring_within_90_days"],
        total_contract_value=dashboard_data["total_contract_value"],
        total_active_value=dashboard_data["total_active_value"],
        contracts_by_department=dashboard_data["contracts_by_department"],
        contracts_by_status=dashboard_data["contracts_by_status"],
        contracts_by_currency=dashboard_data["contracts_by_currency"],
        recent_contracts=recent_contracts,
        expiring_soon=expiring_soon
    )


@router.get("/pending-documents", response_model=PendingDocumentsWorkbasket)
def get_pending_termination_documents(
    current_user: User = Depends(require_contract_admin),
    db: Session = Depends(get_db)
):
    """
    Get workbasket of contracts pending termination documents (DSA-97)
    Only accessible by Contract Admin
    """
    contract_service = ContractService(db)
    pending_contracts = contract_service.get_pending_termination_documents()
    
    # Build contract summary items
    def build_summary_item(contract):
        today = date.today()
        days_until_exp = (contract.end_date - today).days if contract.end_date >= today else None
        
        return ContractSummaryItem(
            id=contract.id,
            contract_id=contract.contract_id,
            vendor_name=contract.vendor.vendor_name,
            contract_description=contract.contract_description,
            contract_type=contract.contract_type,
            start_date=contract.start_date,
            end_date=contract.end_date,
            status=contract.status,
            contract_amount=contract.contract_amount,
            contract_currency=contract.contract_currency,
            department=contract.department,
            contract_owner_name=f"{contract.contract_owner.first_name} {contract.contract_owner.last_name}",
            days_until_expiration=days_until_exp
        )
    
    pending_items = [build_summary_item(c) for c in pending_contracts]
    
    return PendingDocumentsWorkbasket(
        total_pending=len(pending_items),
        pending_contracts=pending_items
    )


@router.post("/contracts/{contract_id}/actions", response_model=ContractActionResponse)
def perform_contract_action(
    contract_id: int,
    action_request: ContractActionRequest,
    current_user: User = Depends(require_contract_manager),
    db: Session = Depends(get_db)
):
    """
    Perform action on contract: extend or terminate (DSA-92, DSA-98)
    Available to Contract Manager and Contract Admin
    """
    contract_service = ContractService(db)
    
    # Get contract to verify ownership or admin rights
    contract = contract_service.get_contract_by_id(contract_id)
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found"
        )
    
    # Check permissions: owner or admin
    is_owner = contract.contract_owner_id == current_user.id
    is_admin = current_user.role == UserRole.CONTRACT_ADMIN
    
    if not (is_owner or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to modify this contract"
        )
    
    modified_by = current_user.email
    
    if action_request.action == "extend":
        if not action_request.new_end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="new_end_date is required for extend action"
            )
        
        updated_contract = contract_service.extend_contract(
            contract_id,
            action_request.new_end_date,
            modified_by
        )
        
        return ContractActionResponse(
            success=True,
            message=f"Contract extended until {action_request.new_end_date}",
            contract_id=updated_contract.contract_id,
            action_performed="extend"
        )
    
    elif action_request.action == "terminate":
        reason = action_request.termination_reason or "No reason provided"
        
        updated_contract = contract_service.terminate_contract(
            contract_id,
            reason,
            modified_by
        )
        
        return ContractActionResponse(
            success=True,
            message=f"Contract terminated. Reason: {reason}",
            contract_id=updated_contract.contract_id,
            action_performed="terminate"
        )
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action: {action_request.action}. Must be 'extend' or 'terminate'"
        )


# NEW ENDPOINTS - Contract Owner and Backup Dashboards

@router.get("/owner/expiring-contracts")
def get_owner_expiring_contracts(
    owner_id: int,
    days_threshold: int = 90,
    sort_by: Optional[str] = "end_date",
    sort_order: Optional[str] = "asc",
    db: Session = Depends(get_db)
):
    """
    Get expiring contracts for Contract Owner.
    Shows contracts expiring within threshold (default 90 days).
    """
    from app.models.contract import Contract
    from datetime import date, timedelta
    
    # Verify owner exists
    owner = db.query(User).filter(User.id == owner_id).first()
    if not owner:
        raise HTTPException(
            status_code=404,
            detail="Contract owner not found"
        )
    
    # Calculate threshold
    threshold_date = date.today() + timedelta(days=days_threshold)
    
    # Query expiring contracts
    contracts = db.query(Contract).filter(
        Contract.contract_owner_id == owner_id,
        Contract.end_date <= threshold_date,
        Contract.end_date >= date.today()
    ).all()
    
    # Format response
    result = []
    for contract in contracts:
        days_until = (contract.end_date - date.today()).days
        result.append({
            "id": contract.id,
            "contract_id": contract.contract_id,
            "vendor_name": contract.vendor.vendor_name,
            "type": contract.contract_type.value if hasattr(contract.contract_type, 'value') else contract.contract_type,
            "description": contract.contract_description,
            "department": contract.department.value if hasattr(contract.department, 'value') else contract.department,
            "owner": f"{owner.first_name} {owner.last_name}",
            "expiration_date": contract.end_date.isoformat(),
            "days_until_expiration": days_until,
            "status": contract.status.value if hasattr(contract.status, 'value') else contract.status
        })
    
    return result


@router.get("/owner/pending-terminations")
def get_owner_pending_terminations(
    owner_id: int,
    db: Session = Depends(get_db)
):
    """
    Get contracts with pending termination documents for Contract Owner.
    """
    from app.models.contract import Contract
    
    # Verify owner exists
    owner = db.query(User).filter(User.id == owner_id).first()
    if not owner:
        raise HTTPException(
            status_code=404,
            detail="Contract owner not found"
        )
    
    # Query pending termination contracts
    contracts = db.query(Contract).filter(
        Contract.contract_owner_id == owner_id,
        Contract.status == "Termination Pending – Documents Required"
    ).all()
    
    # Format response
    result = []
    for contract in contracts:
        pending_docs = []
        if not hasattr(contract, 'termination_letter_path') or not contract.termination_letter_path:
            pending_docs.append("Termination Letter")
        if not hasattr(contract, 'final_invoice_path') or not contract.final_invoice_path:
            pending_docs.append("Final Invoice")
            
        result.append({
            "id": contract.id,
            "contract_id": contract.contract_id,
            "vendor_name": contract.vendor.vendor_name,
            "type": contract.contract_type.value if hasattr(contract.contract_type, 'value') else contract.contract_type,
            "description": contract.contract_description,
            "department": contract.department.value if hasattr(contract.department, 'value') else contract.department,
            "owner": f"{owner.first_name} {owner.last_name}",
            "expiration_date": contract.end_date.isoformat(),
            "status": contract.status.value if hasattr(contract.status, 'value') else contract.status,
            "pending_documents": pending_docs
        })
    
    return result


@router.get("/backup/expiring-contracts")
def get_backup_expiring_contracts(
    backup_id: int,
    days_threshold: int = 90,
    db: Session = Depends(get_db)
):
    """
    Get expiring contracts for Contract Manager Backup.
    Shows contracts expiring within threshold (default 90 days).
    """
    from app.models.contract import Contract
    from datetime import date, timedelta
    
    # Verify backup exists
    backup = db.query(User).filter(User.id == backup_id).first()
    if not backup:
        raise HTTPException(
            status_code=404,
            detail="Contract manager backup not found"
        )
    
    # Calculate threshold
    threshold_date = date.today() + timedelta(days=days_threshold)
    
    # Query expiring contracts where user is backup
    contracts = db.query(Contract).filter(
        Contract.contract_manager_backup_id == backup_id,
        Contract.end_date <= threshold_date,
        Contract.end_date >= date.today()
    ).all()
    
    # Format response
    result = []
    for contract in contracts:
        owner = db.query(User).filter(User.id == contract.contract_owner_id).first()
        days_until = (contract.end_date - date.today()).days
        result.append({
            "id": contract.id,
            "contract_id": contract.contract_id,
            "vendor_name": contract.vendor.vendor_name,
            "type": contract.contract_type.value if hasattr(contract.contract_type, 'value') else contract.contract_type,
            "description": contract.contract_description,
            "department": contract.department.value if hasattr(contract.department, 'value') else contract.department,
            "owner": f"{owner.first_name} {owner.last_name}" if owner else "Unknown",
            "expiration_date": contract.end_date.isoformat(),
            "days_until_expiration": days_until,
            "status": contract.status.value if hasattr(contract.status, 'value') else contract.status
        })
    
    return result


@router.get("/backup/pending-terminations")
def get_backup_pending_terminations(
    backup_id: int,
    db: Session = Depends(get_db)
):
    """
    Get contracts with pending termination documents for Contract Manager Backup.
    """
    from app.models.contract import Contract
    
    # Verify backup exists
    backup = db.query(User).filter(User.id == backup_id).first()
    if not backup:
        raise HTTPException(
            status_code=404,
            detail="Contract manager backup not found"
        )
    
    # Query pending termination contracts where user is backup
    contracts = db.query(Contract).filter(
        Contract.contract_manager_backup_id == backup_id,
        Contract.status == "Termination Pending – Documents Required"
    ).all()
    
    # Format response
    result = []
    for contract in contracts:
        owner = db.query(User).filter(User.id == contract.contract_owner_id).first()
        pending_docs = []
        if not hasattr(contract, 'termination_letter_path') or not contract.termination_letter_path:
            pending_docs.append("Termination Letter")
        if not hasattr(contract, 'final_invoice_path') or not contract.final_invoice_path:
            pending_docs.append("Final Invoice")
            
        result.append({
            "id": contract.id,
            "contract_id": contract.contract_id,
            "vendor_name": contract.vendor.vendor_name,
            "type": contract.contract_type.value if hasattr(contract.contract_type, 'value') else contract.contract_type,
            "description": contract.contract_description,
            "department": contract.department.value if hasattr(contract.department, 'value') else contract.department,
            "owner": f"{owner.first_name} {owner.last_name}" if owner else "Unknown",
            "expiration_date": contract.end_date.isoformat(),
            "status": contract.status.value if hasattr(contract.status, 'value') else contract.status,
            "pending_documents": pending_docs
        })
    
    return result