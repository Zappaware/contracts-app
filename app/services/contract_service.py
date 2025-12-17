from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, date, timedelta
from decimal import Decimal
import os
import uuid
from fastapi import UploadFile, HTTPException

from app.models.contract import Contract, User, ContractDocument, ContractStatusType
from app.models.vendor import Vendor
from app.schemas.contract import ContractCreate, ContractUpdate, UserCreate, ContractSummary
from app.services.vendor_service import VendorService


class ContractService:
    def __init__(self, db: Session):
        self.db = db
        self.vendor_service = VendorService(db)

    def generate_contract_id(self) -> str:
        """
        Generate unique contract ID with CT prefix
        Format: CT1, CT2, CT3, etc.
        """
        # Get all existing contract IDs with CT prefix
        existing_contracts = (
            self.db.query(Contract.contract_id)
            .filter(Contract.contract_id.like("CT%"))
            .all()
        )
        
        # Extract numeric parts and find the maximum
        existing_numbers = []
        for (contract_id,) in existing_contracts:
            try:
                number = int(contract_id[2:])  # Remove CT prefix
                existing_numbers.append(number)
            except ValueError:
                continue
        
        # Generate next number
        if existing_numbers:
            next_number = max(existing_numbers) + 1
        else:
            next_number = 1
        
        new_contract_id = f"CT{next_number}"
        
        # Verify it doesn't exist (safety check)
        existing = self.db.query(Contract).filter(
            Contract.contract_id == new_contract_id
        ).first()
        
        if existing:
            # If somehow it exists, keep incrementing until we find a free one
            while existing:
                next_number += 1
                new_contract_id = f"CT{next_number}"
                existing = self.db.query(Contract).filter(
                    Contract.contract_id == new_contract_id
                ).first()
        
        return new_contract_id

    def generate_user_id(self) -> str:
        """
        Generate unique user ID with U prefix
        Format: U1, U2, U3, etc.
        """
        # Get all existing user IDs with U prefix
        existing_users = (
            self.db.query(User.user_id)
            .filter(User.user_id.like("U%"))
            .all()
        )
        
        # Extract numeric parts and find the maximum
        existing_numbers = []
        for (user_id,) in existing_users:
            try:
                number = int(user_id[1:])  # Remove U prefix
                existing_numbers.append(number)
            except ValueError:
                continue
        
        # Generate next number
        if existing_numbers:
            next_number = max(existing_numbers) + 1
        else:
            next_number = 1
        
        new_user_id = f"U{next_number}"
        
        # Verify it doesn't exist (safety check)
        existing = self.db.query(User).filter(
            User.user_id == new_user_id
        ).first()
        
        if existing:
            # If somehow it exists, keep incrementing until we find a free one
            while existing:
                next_number += 1
                new_user_id = f"U{next_number}"
                existing = self.db.query(User).filter(
                    User.user_id == new_user_id
                ).first()
        
        return new_user_id

    def validate_contract_creation_requirements(self, contract_data: ContractCreate) -> List[str]:
        """
        Validate all contract creation requirements and return list of errors
        """
        errors = []
        
        # Check if vendor exists
        vendor = self.db.query(Vendor).filter(Vendor.id == contract_data.vendor_id).first()
        if not vendor:
            errors.append("Selected vendor does not exist")
        
        # Check if users exist
        users_to_check = [
            (contract_data.contract_owner_id, "Contract Owner"),
            (contract_data.contract_owner_backup_id, "Contract Owner Backup"),
            (contract_data.contract_owner_manager_id, "Contract Owner Manager")
        ]
        
        for user_id, role in users_to_check:
            user = self.db.query(User).filter(User.id == user_id, User.is_active == True).first()
            if not user:
                errors.append(f"{role} does not exist or is inactive")
        
        # Check date logic
        if contract_data.end_date <= contract_data.start_date:
            errors.append("Contract end date must be after start date")
        
        # Check if start date is not too far in the past (optional business rule)
        if contract_data.start_date < date.today() - timedelta(days=365):
            errors.append("Contract start date cannot be more than 1 year in the past")
        
        return errors

    def create_contract(self, contract_data: ContractCreate) -> Contract:
        """
        Create a new contract with all related data
        """
        # Generate unique contract ID
        contract_id = self.generate_contract_id()
        
        # Create contract record
        contract = Contract(
            contract_id=contract_id,
            vendor_id=contract_data.vendor_id,
            contract_description=contract_data.contract_description,
            contract_type=contract_data.contract_type,
            start_date=contract_data.start_date,
            end_date=contract_data.end_date,
            automatic_renewal=contract_data.automatic_renewal,
            renewal_period=contract_data.renewal_period,
            department=contract_data.department,
            contract_amount=contract_data.contract_amount,
            contract_currency=contract_data.contract_currency,
            payment_method=contract_data.payment_method,
            termination_notice_period=contract_data.termination_notice_period,
            expiration_notice_frequency=contract_data.expiration_notice_frequency,
            contract_owner_id=contract_data.contract_owner_id,
            contract_owner_backup_id=contract_data.contract_owner_backup_id,
            contract_owner_manager_id=contract_data.contract_owner_manager_id
        )
        
        self.db.add(contract)
        self.db.commit()
        self.db.refresh(contract)
        
        return contract

    def update_contract(self, contract_id: int, contract_data: ContractUpdate, modified_by: str) -> Contract:
        """
        Update existing contract with audit trail
        """
        contract = self.get_contract_by_id(contract_id)
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")
        
        # Update only provided fields
        update_data = contract_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(contract, field, value)
        
        # Update audit trail
        contract.last_modified_by = modified_by
        contract.last_modified_date = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(contract)
        return contract

    def check_and_update_expired_contracts(self) -> int:
        """
        Auto-update contracts that have passed end_date to Expired status
        Returns number of contracts updated
        """
        expired_contracts = self.db.query(Contract).filter(
            Contract.end_date < date.today(),
            Contract.status == ContractStatusType.ACTIVE
        ).all()
        
        for contract in expired_contracts:
            contract.status = ContractStatusType.EXPIRED
            contract.last_modified_by = "SYSTEM"
            contract.last_modified_date = datetime.utcnow()
        
        if expired_contracts:
            self.db.commit()
        
        return len(expired_contracts)

    async def upload_contract_document(
        self,
        contract_id: int,
        file: UploadFile,
        custom_document_name: str,
        document_signed_date: date
    ) -> ContractDocument:
        """
        Upload and save contract document with custom name and signed date
        """
        # Validate PDF file
        if not self.vendor_service.validate_pdf_file(file):
            raise HTTPException(status_code=400, detail="Only valid PDF files are allowed")
        
        # Validate custom document name
        if not self.vendor_service.validate_custom_document_name(custom_document_name):
            raise HTTPException(
                status_code=400,
                detail="Document name can only contain letters, numbers, spaces, and the characters: - | &"
            )
        
        # Validate document signed date
        if document_signed_date > date.today():
            raise HTTPException(status_code=400, detail="Document signed date cannot be in the future")
        
        # Get contract
        contract = self.db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")
        
        # Save file
        file_path = await self.save_uploaded_file(file, contract.contract_id, "contract")
        
        # Create document record
        document = ContractDocument(
            contract_id=contract_id,
            file_name=file.filename,
            custom_document_name=custom_document_name.strip(),
            document_signed_date=document_signed_date,
            file_path=file_path,
            file_size=file.size,
            content_type=file.content_type
        )
        
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        
        return document

    async def save_uploaded_file(self, file: UploadFile, contract_id: str, document_type: str) -> str:
        """
        Save uploaded file to disk and return file path
        """
        # Create uploads directory if it doesn't exist
        upload_dir = os.path.join("uploads", "contracts", contract_id)
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{document_type}_{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        return file_path

    def get_contract_by_id(self, contract_id: int) -> Optional[Contract]:
        """
        Get contract by ID with all related data
        """
        return (
            self.db.query(Contract)
            .filter(Contract.id == contract_id)
            .first()
        )

    def get_contract_by_contract_id(self, contract_id: str) -> Optional[Contract]:
        """
        Get contract by contract_id (CT1, CT2, etc.) with all related data
        """
        return (
            self.db.query(Contract)
            .filter(Contract.contract_id == contract_id)
            .first()
        )

    def get_contracts(self, skip: int = 0, limit: int = 100) -> List[Contract]:
        """
        Get list of contracts with pagination
        """
        return (
            self.db.query(Contract)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def search_and_filter_contracts(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        status: Optional[ContractStatusType] = None,
        contract_type: Optional[str] = None,
        department: Optional[str] = None,
        owner_id: Optional[int] = None,
        vendor_id: Optional[int] = None,
        expiring_soon: Optional[bool] = None
    ) -> tuple[List[Contract], int]:
        """
        Advanced search and filter contracts with pagination
        Returns: (contracts, total_count)
        """
        query = self.db.query(Contract)
        
        # Apply filters
        if status:
            query = query.filter(Contract.status == status)
        
        if contract_type:
            query = query.filter(Contract.contract_type == contract_type)
        
        if department:
            query = query.filter(Contract.department == department)
        
        if owner_id:
            query = query.filter(Contract.contract_owner_id == owner_id)
        
        if vendor_id:
            query = query.filter(Contract.vendor_id == vendor_id)
        
        if expiring_soon:
            cutoff_date = date.today() + timedelta(days=30)
            query = query.filter(
                Contract.end_date <= cutoff_date,
                Contract.end_date >= date.today()
            )
        
        # Apply search (keyword search across multiple fields)
        if search:
            search_term = f"%{search}%"
            query = query.join(Contract.vendor).join(Contract.contract_owner).filter(
                (Contract.contract_id.ilike(search_term)) |
                (Contract.contract_description.ilike(search_term)) |
                (Vendor.vendor_name.ilike(search_term)) |
                (User.first_name.ilike(search_term)) |
                (User.last_name.ilike(search_term))
            )
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply pagination
        contracts = query.offset(skip).limit(limit).all()
        
        return contracts, total_count

    def get_contracts_by_vendor(self, vendor_id: int) -> List[Contract]:
        """
        Get all contracts for a specific vendor
        """
        return (
            self.db.query(Contract)
            .filter(Contract.vendor_id == vendor_id)
            .all()
        )

    def get_expiring_contracts(self, days_ahead: int = 30) -> List[Contract]:
        """
        Get contracts expiring within specified days
        """
        cutoff_date = date.today() + timedelta(days=days_ahead)
        
        return (
            self.db.query(Contract)
            .filter(Contract.end_date <= cutoff_date)
            .filter(Contract.end_date >= date.today())
            .all()
        )
    
    def get_contracts_with_no_documents(
        self,
        skip: int = 0,
        limit: int = 1000
    ) -> tuple[List[Contract], int]:
        """
        Get active contracts that have no documents uploaded
        Returns: (contracts, total_count)
        """
        # Query active contracts that have no associated documents
        query = (
            self.db.query(Contract)
            .outerjoin(ContractDocument, Contract.id == ContractDocument.contract_id)
            .filter(Contract.status == ContractStatusType.ACTIVE)
            .filter(ContractDocument.id == None)  # No documents
        )
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply pagination
        contracts = query.offset(skip).limit(limit).all()
        
        return contracts, total_count
    
    def get_contracts_needing_review(
        self,
        skip: int = 0,
        limit: int = 1000,
        days_ahead: int = 90
    ) -> tuple[List[Contract], int]:
        """
        Get active contracts expiring within specified days that need review
        (contracts expiring soon, regardless of document status)
        Returns: (contracts, total_count)
        """
        cutoff_date = date.today() + timedelta(days=days_ahead)
        
        query = (
            self.db.query(Contract)
            .filter(Contract.status == ContractStatusType.ACTIVE)
            .filter(Contract.end_date <= cutoff_date)
            .filter(Contract.end_date >= date.today())
        )
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply pagination
        contracts = query.offset(skip).limit(limit).all()
        
        return contracts, total_count

    def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user
        """
        # Generate unique user ID
        user_id = self.generate_user_id()
        
        # Create user record
        user = User(
            user_id=user_id,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            email=user_data.email,
            department=user_data.department,
            position=user_data.position
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user

    def get_users(self, active_only: bool = True) -> List[User]:
        """
        Get list of users
        """
        query = self.db.query(User)
        if active_only:
            query = query.filter(User.is_active == True)
        
        return query.all()

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Get user by ID
        """
        return self.db.query(User).filter(User.id == user_id).first()

    def get_contract_summary(self) -> ContractSummary:
        """
        Get contract summary statistics
        """
        today = date.today()
        
        # Total contracts
        total_contracts = self.db.query(func.count(Contract.id)).scalar()
        
        # Active contracts (not expired)
        active_contracts = (
            self.db.query(func.count(Contract.id))
            .filter(Contract.end_date >= today)
            .scalar()
        )
        
        # Expiring soon (within 30 days)
        expiring_soon = (
            self.db.query(func.count(Contract.id))
            .filter(Contract.end_date >= today)
            .filter(Contract.end_date <= today + timedelta(days=30))
            .scalar()
        )
        
        # Total contract value (active contracts only)
        total_value_result = (
            self.db.query(func.sum(Contract.contract_amount))
            .filter(Contract.end_date >= today)
            .scalar()
        )
        total_contract_value = total_value_result or Decimal('0')
        
        # Contracts by department
        dept_stats = (
            self.db.query(Contract.department, func.count(Contract.id))
            .filter(Contract.end_date >= today)
            .group_by(Contract.department)
            .all()
        )
        contracts_by_department = {dept.value: count for dept, count in dept_stats}
        
        # Contracts by currency
        currency_stats = (
            self.db.query(Contract.contract_currency, func.count(Contract.id))
            .filter(Contract.end_date >= today)
            .group_by(Contract.contract_currency)
            .all()
        )
        contracts_by_currency = {curr.value: count for curr, count in currency_stats}
        
        return ContractSummary(
            total_contracts=total_contracts,
            active_contracts=active_contracts,
            expiring_soon=expiring_soon,
            total_contract_value=total_contract_value,
            contracts_by_department=contracts_by_department,
            contracts_by_currency=contracts_by_currency
        )

    def get_manager_dashboard_data(self, user_id: int) -> dict:
        """
        Get dashboard data for Contract Manager (DSA-90, DSA-91)
        """
        today = date.today()
        cutoff_30_days = today + timedelta(days=30)
        
        # Get all contracts owned by this manager
        owned_contracts = (
            self.db.query(Contract)
            .filter(Contract.contract_owner_id == user_id)
            .all()
        )
        
        # Statistics
        total_owned = len(owned_contracts)
        active = len([c for c in owned_contracts if c.status == ContractStatusType.ACTIVE])
        expired = len([c for c in owned_contracts if c.status == ContractStatusType.EXPIRED])
        
        # Expiring soon (within 30 days)
        expiring_contracts = [
            c for c in owned_contracts
            if c.end_date <= cutoff_30_days and c.end_date >= today
            and c.status == ContractStatusType.ACTIVE
        ]
        
        return {
            "total_owned_contracts": total_owned,
            "active_contracts": active,
            "expiring_soon_contracts": len(expiring_contracts),
            "expired_contracts": expired,
            "expiring_contracts": expiring_contracts,
            "owned_contracts": owned_contracts
        }

    def get_admin_dashboard_data(self) -> dict:
        """
        Get dashboard data for Contract Admin (DSA-96)
        """
        today = date.today()
        
        # Overall statistics
        total_contracts = self.db.query(func.count(Contract.id)).scalar()
        
        active_contracts = (
            self.db.query(func.count(Contract.id))
            .filter(Contract.status == ContractStatusType.ACTIVE.value)
            .scalar()
        )
        
        expired_contracts = (
            self.db.query(func.count(Contract.id))
            .filter(Contract.status == ContractStatusType.EXPIRED.value)
            .scalar()
        )
        
        terminated_contracts = (
            self.db.query(func.count(Contract.id))
            .filter(Contract.status == ContractStatusType.TERMINATED.value)
            .scalar()
        )
        
        # Expiring contracts by timeframe
        expiring_30 = (
            self.db.query(func.count(Contract.id))
            .filter(
                Contract.end_date >= today,
                Contract.end_date <= today + timedelta(days=30),
                Contract.status == ContractStatusType.ACTIVE.value
            )
            .scalar()
        )
        
        expiring_60 = (
            self.db.query(func.count(Contract.id))
            .filter(
                Contract.end_date >= today,
                Contract.end_date <= today + timedelta(days=60),
                Contract.status == ContractStatusType.ACTIVE.value
            )
            .scalar()
        )
        
        expiring_90 = (
            self.db.query(func.count(Contract.id))
            .filter(
                Contract.end_date >= today,
                Contract.end_date <= today + timedelta(days=90),
                Contract.status == ContractStatusType.ACTIVE.value
            )
            .scalar()
        )
        
        # Financial overview
        total_value_result = (
            self.db.query(func.sum(Contract.contract_amount))
            .scalar()
        )
        total_contract_value = total_value_result or Decimal('0')
        
        active_value_result = (
            self.db.query(func.sum(Contract.contract_amount))
            .filter(Contract.status == ContractStatusType.ACTIVE.value)
            .scalar()
        )
        total_active_value = active_value_result or Decimal('0')
        
        # Breakdown by department
        dept_stats = (
            self.db.query(Contract.department, func.count(Contract.id))
            .group_by(Contract.department)
            .all()
        )
        contracts_by_department = {dept.value: count for dept, count in dept_stats}
        
        # Breakdown by status
        status_stats = (
            self.db.query(Contract.status, func.count(Contract.id))
            .group_by(Contract.status)
            .all()
        )
        contracts_by_status = {status.value: count for status, count in status_stats}
        
        # Breakdown by currency
        currency_stats = (
            self.db.query(Contract.contract_currency, func.count(Contract.id))
            .group_by(Contract.contract_currency)
            .all()
        )
        contracts_by_currency = {curr.value: count for curr, count in currency_stats}
        
        # Recent contracts (last 10)
        recent_contracts = (
            self.db.query(Contract)
            .order_by(Contract.created_at.desc())
            .limit(10)
            .all()
        )
        
        # Expiring soon
        expiring_soon = (
            self.db.query(Contract)
            .filter(
                Contract.end_date >= today,
                Contract.end_date <= today + timedelta(days=30),
                Contract.status == ContractStatusType.ACTIVE.value
            )
            .order_by(Contract.end_date)
            .all()
        )
        
        return {
            "total_contracts": total_contracts,
            "active_contracts": active_contracts,
            "expired_contracts": expired_contracts,
            "terminated_contracts": terminated_contracts,
            "expiring_within_30_days": expiring_30,
            "expiring_within_60_days": expiring_60,
            "expiring_within_90_days": expiring_90,
            "total_contract_value": total_contract_value,
            "total_active_value": total_active_value,
            "contracts_by_department": contracts_by_department,
            "contracts_by_status": contracts_by_status,
            "contracts_by_currency": contracts_by_currency,
            "recent_contracts": recent_contracts,
            "expiring_soon": expiring_soon
        }

    def get_pending_termination_documents(self) -> list:
        """
        Get contracts pending termination documents (DSA-97)
        """
        return (
            self.db.query(Contract)
            .filter(Contract.contract_termination == "Yes")
            .filter(Contract.status != ContractStatusType.TERMINATED)
            .all()
        )

    def extend_contract(self, contract_id: int, new_end_date: date, modified_by: str) -> Contract:
        """
        Extend contract end date (DSA-92, DSA-98)
        """
        contract = self.get_contract_by_id(contract_id)
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")
        
        if new_end_date <= contract.end_date:
            raise HTTPException(
                status_code=400,
                detail="New end date must be after current end date"
            )
        
        contract.end_date = new_end_date
        contract.status = ContractStatusType.ACTIVE
        contract.last_modified_by = modified_by
        contract.last_modified_date = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(contract)
        return contract

    def terminate_contract(self, contract_id: int, reason: str, modified_by: str) -> Contract:
        """
        Terminate contract (DSA-92, DSA-98)
        """
        contract = self.get_contract_by_id(contract_id)
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")
        
        if contract.status == ContractStatusType.TERMINATED:
            raise HTTPException(
                status_code=400,
                detail="Contract is already terminated"
            )
        
        contract.status = ContractStatusType.TERMINATED
        contract.contract_termination = "Yes"
        contract.last_modified_by = modified_by
        contract.last_modified_date = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(contract)
        return contract