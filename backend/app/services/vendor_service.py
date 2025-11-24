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
    MaterialOutsourcingType, DueDiligenceRequiredType, DocumentType
)
from app.schemas.vendor import VendorCreate, VendorDocumentUpload
from app.core.config import settings


class VendorService:
    def __init__(self, db: Session):
        self.db = db

    def generate_vendor_id(self, bank_type: str = "AB") -> str:
        """
        Generate unique vendor ID with AB or OB prefix
        Format: AB1, AB2, AB3, OB1, OB2, etc.
        """
        # Get the last vendor ID for the specific bank type
        last_vendor = (
            self.db.query(Vendor)
            .filter(Vendor.vendor_id.like(f"{bank_type}%"))
            .order_by(Vendor.vendor_id.desc())
            .first()
        )
        
        if last_vendor:
            # Extract the numeric part and increment
            try:
                last_number = int(last_vendor.vendor_id[2:])  # Remove AB or OB prefix
                next_number = last_number + 1
            except ValueError:
                next_number = 1
        else:
            next_number = 1
        
        return f"{bank_type}{next_number}"

    def calculate_next_due_diligence_date(
        self, 
        last_due_diligence_date: datetime, 
        material_outsourcing: MaterialOutsourcingType
    ) -> datetime:
        """
        Calculate next required due diligence date based on material outsourcing status
        - Material Outsourcing = YES: add 3 years
        - Material Outsourcing = NO: add 5 years
        """
        if material_outsourcing == MaterialOutsourcingType.YES:
            return last_due_diligence_date + relativedelta(years=3)
        else:
            return last_due_diligence_date + relativedelta(years=5)

    def validate_pdf_file(self, file: UploadFile) -> bool:
        """
        Validate that uploaded file is a valid PDF
        """
        # Check content type
        if file.content_type != 'application/pdf':
            return False
        
        # Read file content for validation
        file_content = file.file.read()
        file.file.seek(0)  # Reset file pointer
        
        # Use python-magic to detect file type
        try:
            file_type = magic.from_buffer(file_content, mime=True)
            if file_type != 'application/pdf':
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
        """
        Validate custom document name - only letters, numbers, and special characters: -, |, &
        """
        import re
        if not name or not name.strip():
            return False
        
        # Only allow letters, numbers, spaces, and special characters: -, |, &
        return bool(re.match(r'^[a-zA-Z0-9\-|&\s]+$', name.strip()))

    async def save_uploaded_file(self, file: UploadFile, vendor_id: str, document_type: str) -> str:
        """
        Save uploaded file to disk and return file path
        """
        # Create uploads directory if it doesn't exist
        upload_dir = os.path.join("uploads", "vendors", vendor_id)
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

    def create_vendor(self, vendor_data: VendorCreate, bank_type: str = "AB") -> Vendor:
        """
        Create a new vendor with all related data
        """
        # Generate unique vendor ID
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

    async def upload_vendor_document(
        self,
        vendor_id: int,
        file: UploadFile,
        document_type: DocumentType,
        custom_document_name: str,
        document_signed_date: datetime
    ) -> VendorDocument:
        """
        Upload and save vendor document with custom name and signed date
        """
        # Validate PDF file
        if not self.validate_pdf_file(file):
            raise HTTPException(status_code=400, detail="Only valid PDF files are allowed")
        
        # Validate custom document name
        if not self.validate_custom_document_name(custom_document_name):
            raise HTTPException(
                status_code=400,
                detail="Document name can only contain letters, numbers, spaces, and the characters: - | &"
            )
        
        # Validate document signed date
        if document_signed_date > datetime.now():
            raise HTTPException(status_code=400, detail="Document signed date cannot be in the future")
        
        # Get vendor
        vendor = self.db.query(Vendor).filter(Vendor.id == vendor_id).first()
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found")
        
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
        """
        Get vendor by ID with all related data
        """
        return (
            self.db.query(Vendor)
            .filter(Vendor.id == vendor_id)
            .first()
        )

    def get_vendor_by_vendor_id(self, vendor_id: str) -> Optional[Vendor]:
        """
        Get vendor by vendor_id (AB1, OB1, etc.) with all related data
        """
        return (
            self.db.query(Vendor)
            .filter(Vendor.vendor_id == vendor_id)
            .first()
        )

    def get_vendors(self, skip: int = 0, limit: int = 100) -> List[Vendor]:
        """
        Get list of vendors with pagination
        """
        return (
            self.db.query(Vendor)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def validate_vendor_creation_requirements(self, vendor_data: VendorCreate) -> List[str]:
        """
        Validate all vendor creation requirements and return list of errors
        """
        errors = []
        
        # Check if CIF is required and provided
        if vendor_data.bank_customer.value in ["Aruba Bank", "Orco Bank"]:
            if not vendor_data.cif:
                errors.append("CIF is required when bank customer is Aruba Bank or Orco Bank")
        
        # Check due diligence requirements
        if vendor_data.due_diligence_required == DueDiligenceRequiredType.YES:
            if not vendor_data.last_due_diligence_date:
                errors.append("Last due diligence date is required when due diligence is required")
            if not vendor_data.next_required_due_diligence_alert_frequency:
                errors.append("Alert frequency is required when due diligence is required")
        
        # Validate address requirements based on country
        aruba_countries = ['aruba', 'curacao', 'bonaire', 'saint martin']
        is_aruba_country = vendor_data.vendor_country.lower() in aruba_countries
        
        if is_aruba_country:
            # For Aruba countries, only address is required
            for address in vendor_data.addresses:
                if address.city or address.state or address.zip_code:
                    errors.append("City, State, and Zip Code should not be provided for Aruba countries")
        
        return errors

    def get_required_documents_for_vendor(self, vendor_data: VendorCreate) -> List[DocumentType]:
        """
        Get list of required documents based on vendor configuration
        """
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
        """
        Get list of optional documents based on vendor configuration
        """
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
        """
        Get list of required documents based on vendor configuration (direct values)
        """
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
        """
        Get list of optional documents based on vendor configuration (direct values)
        """
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