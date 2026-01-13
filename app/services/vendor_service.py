from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import os
import uuid
from fastapi import UploadFile, HTTPException
import magic
import PyPDF2
import io

from app.models.vendor import (
    Vendor, VendorAddress, VendorEmail, VendorPhone, VendorDocument,
    MaterialOutsourcingType, DueDiligenceRequiredType, DocumentType, VendorStatusType
)
from app.schemas.vendor import VendorCreate, VendorUpdate
from app.core.constants import (
    ErrorMessages,
    HTTPStatus,
    VendorPrefix,
    DueDiligenceConstants,
    FileConstants,
    VendorCountry
)


class VendorService:
    def __init__(self, db: Session):
        self.db = db

    def generate_vendor_id(self, bank_type: str = VendorPrefix.ARUBA_BANK.value) -> str:
        """
        Generate unique vendor ID with proper numeric ordering.
        Format: AB1, AB2, AB3, etc. (for Aruba Bank) or OB1, OB2, OB3, etc. (for Orco Bank)
        """
        # Get all existing vendor IDs with this bank prefix
        existing_vendors = (
            self.db.query(Vendor.vendor_id)
            .filter(Vendor.vendor_id.like(f"{bank_type}%"))
            .all()
        )
        
        # Extract numeric parts and find the maximum
        existing_numbers = []
        for (vendor_id,) in existing_vendors:
            try:
                number = int(vendor_id[2:])  # Remove AB or OB prefix
                existing_numbers.append(number)
            except ValueError:
                continue
        
        # Generate next number
        if existing_numbers:
            next_number = max(existing_numbers) + 1
        else:
            next_number = 1
        
        new_vendor_id = f"{bank_type}{next_number}"
        
        # Verify it doesn't exist (safety check)
        existing = self.db.query(Vendor).filter(
            Vendor.vendor_id == new_vendor_id
        ).first()
        
        if existing:
            # If somehow it exists, keep incrementing until we find a free ID
            while existing:
                next_number += 1
                new_vendor_id = f"{bank_type}{next_number}"
                existing = self.db.query(Vendor).filter(
                    Vendor.vendor_id == new_vendor_id
                ).first()
        
        print(f"Generated vendor ID: {new_vendor_id}")
        return new_vendor_id

    def calculate_next_due_diligence_date(
        self,
        last_due_diligence_date: datetime,
        material_outsourcing: MaterialOutsourcingType
    ) -> datetime:
        years = (DueDiligenceConstants.MATERIAL_OUTSOURCING_YEARS
                if material_outsourcing == MaterialOutsourcingType.YES
                else DueDiligenceConstants.NON_MATERIAL_OUTSOURCING_YEARS)
        return last_due_diligence_date + relativedelta(years=years)

    def validate_pdf_file(self, file: UploadFile) -> bool:
        if not file or not file.filename:
            return False
        
        if file.content_type not in FileConstants.ALLOWED_FILE_TYPES:
            return False
        
        # Read file content for validation
        try:
            file_content = file.file.read()
            file.file.seek(0)  # Reset file pointer
        except Exception:
            return False
        
        # Check if file is empty
        if len(file_content) == 0:
            return False
        
        try:
            file_type = magic.from_buffer(file_content, mime=True)
            if file_type not in FileConstants.ALLOWED_FILE_TYPES:
                return False
        except Exception:
            return False
        
        # Try to read PDF with PyPDF2
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            # Check if PDF has at least one page
            if len(pdf_reader.pages) == 0:
                return False
        except Exception:
            return False
        
        return True

    def validate_custom_document_name(self, name: str) -> bool:
        import re
        if not name or not name.strip():
            return False
        return bool(re.match(r'^[a-zA-Z0-9\-|&\s]+$', name.strip()))

    async def save_uploaded_file(self, file: UploadFile, vendor_id: str, document_type: str) -> str:
        upload_dir = os.path.join(FileConstants.VENDOR_DOCS_DIR, vendor_id)
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

    def create_vendor(self, vendor_data: VendorCreate, bank_type: str = VendorPrefix.ARUBA_BANK.value) -> Vendor:
        vendor_id = self.generate_vendor_id(bank_type)
        
        # Calculate next due diligence date if required
        next_due_diligence_date = None
        if (vendor_data.due_diligence_required == DueDiligenceRequiredType.YES and 
            vendor_data.last_due_diligence_date):
            next_due_diligence_date = self.calculate_next_due_diligence_date(
                vendor_data.last_due_diligence_date,
                vendor_data.material_outsourcing_arrangement
            )
        
        # Create vendor record
        vendor = Vendor(
            vendor_id=vendor_id,
            vendor_name=vendor_data.vendor_name,
            vendor_contact_person=vendor_data.vendor_contact_person,
            vendor_country=vendor_data.vendor_country,
            material_outsourcing_arrangement=vendor_data.material_outsourcing_arrangement,
            bank_customer=vendor_data.bank_customer,
            cif=vendor_data.cif,
            due_diligence_required=vendor_data.due_diligence_required,
            last_due_diligence_date=vendor_data.last_due_diligence_date,
            next_required_due_diligence_date=next_due_diligence_date,
            next_required_due_diligence_alert_frequency=vendor_data.next_required_due_diligence_alert_frequency
        )
        
        self.db.add(vendor)
        self.db.flush()  # Get the vendor ID
        
        # Create addresses
        for i, address_data in enumerate(vendor_data.addresses):
            address = VendorAddress(
                vendor_id=vendor.id,
                address=address_data.address,
                city=address_data.city,
                state=address_data.state,
                zip_code=address_data.zip_code,
                is_primary=(i == 0)  # First address is primary
            )
            self.db.add(address)
        
        # Create emails
        for i, email_data in enumerate(vendor_data.emails):
            email = VendorEmail(
                vendor_id=vendor.id,
                email=email_data.email,
                is_primary=(i == 0)  # First email is primary
            )
            self.db.add(email)
        
        # Create phone numbers
        for i, phone_data in enumerate(vendor_data.phones):
            phone = VendorPhone(
                vendor_id=vendor.id,
                area_code=phone_data.area_code,
                phone_number=phone_data.phone_number,
                is_primary=(i == 0)  # First phone is primary
            )
            self.db.add(phone)
        
        self.db.commit()
        self.db.refresh(vendor)
        
        return vendor

    def update_vendor(self, vendor_id: int, vendor_data: VendorUpdate, modified_by: str) -> Vendor:
        vendor = self.get_vendor_by_id(vendor_id)
        if not vendor:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=ErrorMessages.VENDOR_NOT_FOUND
            )
        
        # Update only provided fields
        update_data = vendor_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(vendor, field, value)
        
        # Update audit trail
        vendor.last_modified_by = modified_by
        vendor.last_modified_date = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(vendor)
        return vendor
    
    def update_vendor_primary_email(self, vendor_id: int, new_email: str) -> VendorEmail:
        """Update the primary email for a vendor"""
        vendor = self.get_vendor_by_id(vendor_id)
        if not vendor:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=ErrorMessages.VENDOR_NOT_FOUND
            )
        
        # Get primary email
        primary_email = next((e for e in vendor.emails if e.is_primary), None)
        
        if primary_email:
            # Update existing primary email
            primary_email.email = new_email
        else:
            # Create new primary email if none exists
            primary_email = VendorEmail(
                vendor_id=vendor_id,
                email=new_email,
                is_primary=True
            )
            self.db.add(primary_email)
        
        self.db.commit()
        self.db.refresh(primary_email)
        return primary_email
    
    def update_vendor_primary_phone(self, vendor_id: int, area_code: str, phone_number: str) -> VendorPhone:
        """Update the primary phone for a vendor"""
        vendor = self.get_vendor_by_id(vendor_id)
        if not vendor:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=ErrorMessages.VENDOR_NOT_FOUND
            )
        
        # Get primary phone
        primary_phone = next((p for p in vendor.phones if p.is_primary), None)
        
        if primary_phone:
            # Update existing primary phone
            primary_phone.area_code = area_code
            primary_phone.phone_number = phone_number
        else:
            # Create new primary phone if none exists
            primary_phone = VendorPhone(
                vendor_id=vendor_id,
                area_code=area_code,
                phone_number=phone_number,
                is_primary=True
            )
            self.db.add(primary_phone)
        
        self.db.commit()
        self.db.refresh(primary_phone)
        return primary_phone
    
    def update_vendor_primary_address(
        self, 
        vendor_id: int, 
        address: str, 
        city: str = None, 
        state: str = None, 
        zip_code: str = None
    ) -> VendorAddress:
        """Update the primary address for a vendor"""
        vendor = self.get_vendor_by_id(vendor_id)
        if not vendor:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=ErrorMessages.VENDOR_NOT_FOUND
            )
        
        # Get primary address
        primary_address = next((a for a in vendor.addresses if a.is_primary), None)
        
        if primary_address:
            # Update existing primary address
            primary_address.address = address
            primary_address.city = city
            primary_address.state = state
            primary_address.zip_code = zip_code
        else:
            # Create new primary address if none exists
            primary_address = VendorAddress(
                vendor_id=vendor_id,
                address=address,
                city=city,
                state=state,
                zip_code=zip_code,
                is_primary=True
            )
            self.db.add(primary_address)
        
        self.db.commit()
        self.db.refresh(primary_address)
        return primary_address

    def get_active_vendors(self, skip: int = 0, limit: int = 1000) -> List[Vendor]:
        return (
            self.db.query(Vendor)
            .filter(Vendor.status == VendorStatusType.ACTIVE)
            .offset(skip)
            .limit(limit)
            .all()
        )

    async def upload_vendor_document(
        self,
        vendor_id: int,
        file: UploadFile,
        document_type: DocumentType,
        custom_document_name: str,
        document_signed_date: datetime
    ) -> VendorDocument:
        print(f"    Uploading document: {document_type.value}")
        print(f"      Name: {custom_document_name}")
        print(f"      Signed date: {document_signed_date}")
        print(f"      Current date: {datetime.now()}")
        
        if not self.validate_pdf_file(file):
            print(f"    ❌ Invalid PDF file")
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=ErrorMessages.INVALID_FILE_TYPE
            )
        
        if not self.validate_custom_document_name(custom_document_name):
            print(f"    ❌ Invalid document name")
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail="Document name can only contain letters, numbers, spaces, and the characters: - | &"
            )
        
        # Allow future dates for testing purposes
        # if document_signed_date > datetime.now():
        #     print(f"    ⚠️ Warning: Document signed date is in the future")
        #     raise HTTPException(
        #         status_code=HTTPStatus.BAD_REQUEST,
        #         detail=f"Document signed date cannot be in the future. Date provided: {document_signed_date.date()}, Current date: {datetime.now().date()}"
        #     )
        
        vendor = self.db.query(Vendor).filter(Vendor.id == vendor_id).first()
        if not vendor:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=ErrorMessages.VENDOR_NOT_FOUND
            )
        
        # Save file
        file_path = await self.save_uploaded_file(file, vendor.vendor_id, document_type.value)
        
        # Create document record
        document = VendorDocument(
            vendor_id=vendor_id,
            document_type=document_type,
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

    def get_vendor_by_id(self, vendor_id: int) -> Optional[Vendor]:
        return (
            self.db.query(Vendor)
            .filter(Vendor.id == vendor_id)
            .first()
        )

    def get_vendor_by_vendor_id(self, vendor_id: str) -> Optional[Vendor]:
        return (
            self.db.query(Vendor)
            .filter(Vendor.vendor_id == vendor_id)
            .first()
        )

    def get_vendors(self, skip: int = 0, limit: int = 100) -> List[Vendor]:
        return (
            self.db.query(Vendor)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def validate_vendor_creation_requirements(self, vendor_data: VendorCreate) -> List[str]:
        errors = []
        
        if vendor_data.bank_customer.value in ["Aruba Bank", "Orco Bank"]:
            if not vendor_data.cif:
                errors.append("CIF is required when bank customer is Aruba Bank or Orco Bank")
        
        if vendor_data.due_diligence_required == DueDiligenceRequiredType.YES:
            if not vendor_data.last_due_diligence_date:
                errors.append("Last due diligence date is required when due diligence is required")
            if not vendor_data.next_required_due_diligence_alert_frequency:
                errors.append("Alert frequency is required when due diligence is required")
        
        is_special_country = vendor_data.vendor_country in VendorCountry.NO_EXTRA_ADDRESS_FIELDS
        
        if is_special_country:
            for address in vendor_data.addresses:
                if address.city or address.state or address.zip_code:
                    errors.append("City, State, and Zip Code should not be provided for Aruba countries")
        
        return errors

    def get_required_documents_for_vendor(self, vendor_data: VendorCreate) -> List[DocumentType]:
        required_docs = []
        
        if vendor_data.due_diligence_required == DueDiligenceRequiredType.YES:
            required_docs.extend([
                DocumentType.DUE_DILIGENCE,
                DocumentType.NON_DISCLOSURE_AGREEMENT
            ])
        
        if vendor_data.material_outsourcing_arrangement == MaterialOutsourcingType.YES:
            required_docs.append(DocumentType.RISK_ASSESSMENT_FORM)
        
        return required_docs

    def get_optional_documents_for_vendor(self, vendor_data: VendorCreate) -> List[DocumentType]:
        optional_docs = []
        
        if vendor_data.due_diligence_required == DueDiligenceRequiredType.YES:
            optional_docs.append(DocumentType.INTEGRITY_POLICY)
        
        if vendor_data.material_outsourcing_arrangement == MaterialOutsourcingType.YES:
            optional_docs.extend([
                DocumentType.BUSINESS_CONTINUITY_PLAN,
                DocumentType.DISASTER_RECOVERY_PLAN,
                DocumentType.INSURANCE_POLICY
            ])
        
        return optional_docs

    def get_required_documents_for_vendor_direct(
        self,
        due_diligence_required: DueDiligenceRequiredType,
        material_outsourcing_arrangement: MaterialOutsourcingType
    ) -> List[DocumentType]:
        required_docs = []
        
        if due_diligence_required == DueDiligenceRequiredType.YES:
            required_docs.extend([
                DocumentType.DUE_DILIGENCE,
                DocumentType.NON_DISCLOSURE_AGREEMENT
            ])
        
        if material_outsourcing_arrangement == MaterialOutsourcingType.YES:
            required_docs.append(DocumentType.RISK_ASSESSMENT_FORM)
        
        return required_docs

    def get_optional_documents_for_vendor_direct(
        self,
        due_diligence_required: DueDiligenceRequiredType,
        material_outsourcing_arrangement: MaterialOutsourcingType
    ) -> List[DocumentType]:
        optional_docs = []
        
        if due_diligence_required == DueDiligenceRequiredType.YES:
            optional_docs.append(DocumentType.INTEGRITY_POLICY)
        
        if material_outsourcing_arrangement == MaterialOutsourcingType.YES:
            optional_docs.extend([
                DocumentType.BUSINESS_CONTINUITY_PLAN,
                DocumentType.DISASTER_RECOVERY_PLAN,
                DocumentType.INSURANCE_POLICY
            ])
        
        return optional_docs

    def get_vendors_with_filters(
        self,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[str] = None,
        search: Optional[str] = None
    ):
        """
        Get vendors with advanced filtering and search.
        Returns tuple of (vendors, total_count)
        """
        from app.models.vendor import VendorEmail
        from sqlalchemy import or_
        
        # Base query
        query = self.db.query(Vendor)
        
        # Apply status filter
        if status_filter:
            if status_filter.lower() == "active":
                query = query.filter(Vendor.status == VendorStatusType.ACTIVE)
            elif status_filter.lower() == "inactive":
                query = query.filter(Vendor.status == VendorStatusType.INACTIVE)
        
        # Apply search
        if search:
            search_term = f"%{search}%"
            vendor_search = or_(
                Vendor.vendor_id.ilike(search_term),
                Vendor.vendor_name.ilike(search_term),
                Vendor.vendor_contact_person.ilike(search_term)
            )
            
            # Also search in emails
            email_subquery = self.db.query(VendorEmail.vendor_id).filter(
                VendorEmail.email.ilike(search_term)
            ).subquery()
            
            query = query.filter(
                or_(
                    vendor_search,
                    Vendor.id.in_(email_subquery)
                )
            )
        
        # Get total count
        total_count = query.count()
        
         # Apply pagination - MSSQL requires ORDER BY when using OFFSET
        vendors = query.order_by(Vendor.id).offset(skip).limit(limit).all()
        
        return vendors, total_count

    def get_vendor_profile_with_details(self, vendor_id: int):
        """
        Get vendor profile with enhanced details including
        due diligence status and color coding
        """
        from datetime import date
        
        vendor = self.get_vendor_by_id(vendor_id)
        if not vendor:
            return None
        
        # Check if due diligence is overdue
        is_overdue = False
        if vendor.next_required_due_diligence_date:
            is_overdue = vendor.next_required_due_diligence_date.date() < date.today()
        
        # Get primary email
        primary_email = None
        if vendor.emails:
            primary_email = next(
                (e.email for e in vendor.emails if e.is_primary),
                vendor.emails[0].email
            )
        
        return {
            'vendor': vendor,
            'is_due_diligence_overdue': is_overdue,
            'primary_email': primary_email,
            'status_color': 'green' if vendor.status == VendorStatusType.ACTIVE else 'black',
            'due_diligence_highlight_color': 'red' if is_overdue else None
        }

    def get_vendor_documents_grouped(self, vendor_id: int):
        """
        Get vendor documents grouped by document type
        """
        vendor = self.get_vendor_by_id(vendor_id)
        if not vendor:
            return None
        
        # Group documents by type
        documents_by_type = {}
        for doc in vendor.documents:
            doc_type = doc.document_type.value if hasattr(doc.document_type, 'value') else doc.document_type
            if doc_type not in documents_by_type:
                documents_by_type[doc_type] = []
            documents_by_type[doc_type].append(doc)
        
        return documents_by_type

    def get_vendor_documents_summary(self, vendor_id: int):
        """
        Get summary of vendor contracts and supporting documents
        """
        from app.models.contract import Contract
        
        vendor = self.get_vendor_by_id(vendor_id)
        if not vendor:
            return None
        
        # Count contracts
        contracts_count = self.db.query(Contract).filter(
            Contract.vendor_id == vendor_id
        ).count()
        
        # Count and group supporting documents
        docs_by_type = {}
        for doc in vendor.documents:
            doc_type = doc.document_type.value if hasattr(doc.document_type, 'value') else doc.document_type
            docs_by_type[doc_type] = docs_by_type.get(doc_type, 0) + 1
        
        return {
            'vendor': vendor,
            'contracts_count': contracts_count,
            'supporting_docs_count': len(vendor.documents),
            'docs_by_type': docs_by_type
        }