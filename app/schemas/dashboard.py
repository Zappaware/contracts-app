"""
Dashboard schemas for Contract Manager and Contract Admin
"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import date
from decimal import Decimal

from app.models.contract import (
    ContractStatusType,
    ContractType,
    DepartmentType,
    CurrencyType
)


class ContractSummaryItem(BaseModel):
    """Summary item for dashboard"""
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
    days_until_expiration: Optional[int] = None

    class Config:
        from_attributes = True


class ContractManagerDashboard(BaseModel):
    """
    Dashboard for Contract Manager (DSA-90, DSA-91)
    Shows contracts owned by the manager
    """
    user_id: int
    user_name: str
    role: str
    
    # Owned contracts statistics
    total_owned_contracts: int
    active_contracts: int
    expiring_soon_contracts: int  # Within 30 days
    expired_contracts: int
    
    # Contracts expiring soon (DSA-90)
    expiring_contracts: List[ContractSummaryItem]
    
    # All owned contracts (DSA-91)
    owned_contracts: List[ContractSummaryItem]


class ContractAdminDashboard(BaseModel):
    """
    Dashboard for Contract Admin (DSA-96)
    Shows overview of all contracts in the system
    """
    # Overall statistics
    total_contracts: int
    active_contracts: int
    expired_contracts: int
    terminated_contracts: int
    expiring_within_30_days: int
    expiring_within_60_days: int
    expiring_within_90_days: int
    
    # Financial overview
    total_contract_value: Decimal
    total_active_value: Decimal
    
    # Breakdown by department
    contracts_by_department: dict
    
    # Breakdown by status
    contracts_by_status: dict
    
    # Breakdown by currency
    contracts_by_currency: dict
    
    # Recent contracts
    recent_contracts: List[ContractSummaryItem]
    
    # Contracts requiring attention
    expiring_soon: List[ContractSummaryItem]


class PendingDocumentsWorkbasket(BaseModel):
    """
    Workbasket for pending termination documents (DSA-97)
    """
    total_pending: int
    pending_contracts: List[ContractSummaryItem]


class ContractActionRequest(BaseModel):
    """
    Request to perform action on contract (DSA-92, DSA-98)
    """
    action: str  # "extend" or "terminate"
    new_end_date: Optional[date] = None  # For extend action
    termination_reason: Optional[str] = None  # For terminate action


class ContractActionResponse(BaseModel):
    """
    Response after performing action on contract
    """
    success: bool
    message: str
    contract_id: str
    action_performed: str