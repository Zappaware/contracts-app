#!/usr/bin/env python3
"""
Script to seed initial vendors and contracts into the database
"""
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.vendor import (
    Vendor, VendorAddress, VendorEmail, VendorPhone, VendorDocument,
    MaterialOutsourcingType, DueDiligenceRequiredType, DocumentType,
    VendorStatusType, BankCustomerType, AlertFrequencyType
)
from app.models.contract import (
    Contract, ContractDocument, User,
    ContractType, AutomaticRenewalType, RenewalPeriodType, DepartmentType,
    NoticePeriodType, ExpirationNoticePeriodType, CurrencyType,
    PaymentMethodType, ContractStatusType
)
from datetime import datetime, date, timedelta, timezone
from dateutil.relativedelta import relativedelta
import os
import uuid
import random


def create_dummy_pdf(output_path):
    """
    Create a minimal valid PDF file for testing
    """
    # Ensure directory exists with proper permissions
    dir_path = os.path.dirname(output_path)
    if dir_path:
        # Create directory and all parent directories
        try:
            os.makedirs(dir_path, exist_ok=True, mode=0o755)
        except (OSError, PermissionError):
            # Directory might already exist, that's okay
            pass
        
        # Try to fix permissions on existing directories (but don't fail if we can't)
        try:
            os.chmod(dir_path, 0o755)
            # Also try to fix parent directories
            parent = os.path.dirname(dir_path)
            while parent and parent != dir_path and os.path.exists(parent):
                try:
                    os.chmod(parent, 0o755)
                except (OSError, PermissionError):
                    pass
                parent = os.path.dirname(parent)
                if not parent or parent == '/':
                    break
        except (OSError, PermissionError):
            # Can't change permissions, but directory might still be writable
            pass
    
    # Minimal PDF content
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
>>
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Sample Contract) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000317 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
409
%%EOF
"""
    
    # Verify directory is writable - if not, try to fix permissions (but don't fail if we can't)
    if not os.access(dir_path, os.W_OK):
        # Try to fix directory permissions, but don't fail if we can't
        try:
            os.chmod(dir_path, 0o755)
        except (OSError, PermissionError):
            # If we can't change permissions, check if we can still write
            # (directory might be writable even if we can't chmod it)
            if not os.access(dir_path, os.W_OK):
                raise PermissionError(f"Cannot write to directory {dir_path}. Please run: chmod -R 755 {dir_path} or fix ownership with: chown -R $USER:$USER {dir_path}")
    
    # Remove file if it exists and is read-only
    if os.path.exists(output_path):
        try:
            # Try to make it writable, but don't fail if we can't
            try:
                os.chmod(output_path, 0o644)
            except (OSError, PermissionError):
                pass
            os.remove(output_path)
        except (OSError, PermissionError):
            pass
    
    # Try to write the file
    try:
        with open(output_path, 'wb') as f:
            f.write(pdf_content)
    except PermissionError as e:
        raise PermissionError(f"Cannot write to file {output_path}. Please check directory permissions. Try: chmod -R 755 {dir_path} or chown -R $USER:$USER {dir_path}. Error: {e}")
    
    # Try to set file permissions, but don't fail if we can't
    try:
        os.chmod(output_path, 0o644)
    except (OSError, PermissionError):
        pass  # File was created successfully, permissions are less critical
    
    # Ensure file has proper permissions
    os.chmod(output_path, 0o644)
    
    return output_path


def save_vendor_document(vendor, document_type, doc_name, signed_date):
    """
    Save a vendor document by creating a dummy PDF
    """
    upload_dir = os.path.join("uploads", "vendors", vendor.vendor_id)
    # Create directory and all parent directories with proper permissions
    os.makedirs(upload_dir, exist_ok=True, mode=0o755)
    # Fix permissions on existing directories
    try:
        os.chmod(upload_dir, 0o755)
        # Also ensure parent directories have proper permissions
        parent = os.path.dirname(upload_dir)
        while parent and parent != upload_dir and os.path.exists(parent):
            try:
                os.chmod(parent, 0o755)
            except (OSError, PermissionError):
                pass
            parent = os.path.dirname(parent)
            if not parent or parent == '/':
                break
    except (OSError, PermissionError):
        pass
    
    # Generate unique filename
    unique_filename = f"{document_type.value}_{uuid.uuid4()}.pdf"
    file_path = os.path.join(upload_dir, unique_filename)
    
    # Create dummy PDF
    create_dummy_pdf(file_path)
    
    # Get file size
    file_size = os.path.getsize(file_path)
    
    return file_path, file_size


def save_contract_document(contract, doc_name, signed_date):
    """
    Save a contract document by creating a dummy PDF
    """
    upload_dir = os.path.join("uploads", "contracts", contract.contract_id)
    # Create directory and all parent directories with proper permissions
    os.makedirs(upload_dir, exist_ok=True, mode=0o755)
    # Fix permissions on existing directories
    try:
        os.chmod(upload_dir, 0o755)
        # Also ensure parent directories have proper permissions
        parent = os.path.dirname(upload_dir)
        while parent and parent != upload_dir and os.path.exists(parent):
            try:
                os.chmod(parent, 0o755)
            except (OSError, PermissionError):
                pass
            parent = os.path.dirname(parent)
            if not parent or parent == '/':
                break
    except (OSError, PermissionError):
        pass
    
    # Generate unique filename
    unique_filename = f"contract_{uuid.uuid4()}.pdf"
    file_path = os.path.join(upload_dir, unique_filename)
    
    # Create dummy PDF
    create_dummy_pdf(file_path)
    
    # Get file size
    file_size = os.path.getsize(file_path)
    
    return file_path, file_size


def ensure_uploads_permissions():
    """
    Ensure uploads directory structure exists with proper permissions
    """
    uploads_base = "uploads"
    uploads_vendors = os.path.join(uploads_base, "vendors")
    uploads_contracts = os.path.join(uploads_base, "contracts")
    
    for directory in [uploads_base, uploads_vendors, uploads_contracts]:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True, mode=0o755)
        else:
            try:
                os.chmod(directory, 0o755)
            except (OSError, PermissionError):
                pass  # If we can't change permissions, continue anyway


def seed_vendors_and_contracts():
    db = SessionLocal()
    
    try:
        # Ensure uploads directory structure has proper permissions
        ensure_uploads_permissions()
        # Check if vendors already exist
        existing_vendor_count = db.query(Vendor).count()
        if existing_vendor_count > 0:
            print(f"⚠️  Database already has {existing_vendor_count} vendor(s). Skipping vendor seed.")
            vendors_created = False
        else:
            vendors_created = True
        
        # Check if contracts already exist
        existing_contract_count = db.query(Contract).count()
        if existing_contract_count > 0:
            print(f"⚠️  Database already has {existing_contract_count} contract(s). Skipping contract seed.")
            return
        
        # Get existing users (should be seeded by seed_users.py)
        users = db.query(User).all()
        if len(users) < 3:
            print("❌ Not enough users in database. Please run seed_users.py first.")
            return
        
        print("\n🌱 Starting vendor and contract seeding...\n")
        
        # Create 20 vendors (doubled from 10)
        vendors_data = [
            {
                "vendor_name": "TechCorp Solutions Inc",
                "vendor_contact_person": "Alice Johnson",
                "vendor_country": "United States",
                "bank_customer": BankCustomerType.ARUBA_BANK,
                "cif": "123456",
                "material_outsourcing_arrangement": MaterialOutsourcingType.YES,
                "address": "123 Tech Street",
                "city": "San Francisco",
                "state": "California",
                "zip_code": "94102",
                "email": "contact@techcorp.com",
                "phone": "555-0101"
            },
            {
                "vendor_name": "Global Services Ltd",
                "vendor_contact_person": "Bob Martinez",
                "vendor_country": "Aruba",
                "bank_customer": BankCustomerType.ARUBA_BANK,
                "cif": "234567",
                "material_outsourcing_arrangement": MaterialOutsourcingType.NO,
                "address": "45 Mainstreet",
                "city": "",
                "state": "",
                "zip_code": "",
                "email": "info@globalservices.aw",
                "phone": "297-5550201"
            },
            {
                "vendor_name": "Cloud Computing Partners",
                "vendor_contact_person": "Carol Chen",
                "vendor_country": "Netherlands",
                "bank_customer": BankCustomerType.NONE,
                "cif": None,
                "material_outsourcing_arrangement": MaterialOutsourcingType.YES,
                "address": "789 Innovation Boulevard",
                "city": "Amsterdam",
                "state": "North Holland",
                "zip_code": "1012",
                "email": "partners@cloudcomputing.nl",
                "phone": "+31-20-5550301"
            },
            {
                "vendor_name": "Security Systems Pro",
                "vendor_contact_person": "David Brown",
                "vendor_country": "Canada",
                "bank_customer": BankCustomerType.ORCO_BANK,
                "cif": "345678",
                "material_outsourcing_arrangement": MaterialOutsourcingType.NO,
                "address": "321 Secure Way",
                "city": "Toronto",
                "state": "Ontario",
                "zip_code": "M5H2N2",
                "email": "contact@securitypro.ca",
                "phone": "+1-416-5550401"
            },
            {
                "vendor_name": "DataCenter Solutions",
                "vendor_contact_person": "Emma Wilson",
                "vendor_country": "United States",
                "bank_customer": BankCustomerType.ARUBA_BANK,
                "cif": "456789",
                "material_outsourcing_arrangement": MaterialOutsourcingType.YES,
                "address": "555 Data Drive",
                "city": "New York",
                "state": "New York",
                "zip_code": "10001",
                "email": "info@datacenters.com",
                "phone": "+1-212-5550501"
            },
            {
                "vendor_name": "Consulting Group International",
                "vendor_contact_person": "Frank Garcia",
                "vendor_country": "Mexico",
                "bank_customer": BankCustomerType.NONE,
                "cif": None,
                "material_outsourcing_arrangement": MaterialOutsourcingType.NO,
                "address": "777 Consulting Avenue",
                "city": "Mexico City",
                "state": "CDMX",
                "zip_code": "06600",
                "email": "contact@consulting.mx",
                "phone": "+52-55-5550601"
            },
            {
                "vendor_name": "Software Development Studio",
                "vendor_contact_person": "Grace Lee",
                "vendor_country": "Curacao",
                "bank_customer": BankCustomerType.ORCO_BANK,
                "cif": "567890",
                "material_outsourcing_arrangement": MaterialOutsourcingType.NO,
                "address": "999 Developer Road",
                "city": "",
                "state": "",
                "zip_code": "",
                "email": "dev@softstudio.cw",
                "phone": "+599-9-5550701"
            },
            {
                "vendor_name": "Network Infrastructure Corp",
                "vendor_contact_person": "Henry Taylor",
                "vendor_country": "United States",
                "bank_customer": BankCustomerType.ARUBA_BANK,
                "cif": "678901",
                "material_outsourcing_arrangement": MaterialOutsourcingType.YES,
                "address": "111 Network Lane",
                "city": "Miami",
                "state": "Florida",
                "zip_code": "33101",
                "email": "info@networkinfra.com",
                "phone": "+1-305-5550801"
            },
            {
                "vendor_name": "Business Analytics LLC",
                "vendor_contact_person": "Isabella Rodriguez",
                "vendor_country": "Bonaire",
                "bank_customer": BankCustomerType.NONE,
                "cif": None,
                "material_outsourcing_arrangement": MaterialOutsourcingType.NO,
                "address": "222 Analytics Street",
                "city": "",
                "state": "",
                "zip_code": "",
                "email": "contact@analytics.bq",
                "phone": "+599-7-5550901"
            },
            {
                "vendor_name": "Enterprise Solutions Group",
                "vendor_contact_person": "Jack Anderson",
                "vendor_country": "United States",
                "bank_customer": BankCustomerType.ARUBA_BANK,
                "cif": "789012",
                "material_outsourcing_arrangement": MaterialOutsourcingType.YES,
                "address": "333 Enterprise Parkway",
                "city": "Boston",
                "state": "Massachusetts",
                "zip_code": "02101",
                "email": "solutions@enterprise.com",
                "phone": "+1-617-5551001"
            },
            {
                "vendor_name": "Digital Marketing Agency",
                "vendor_contact_person": "Kate Thompson",
                "vendor_country": "United States",
                "bank_customer": BankCustomerType.ARUBA_BANK,
                "cif": "890123",
                "material_outsourcing_arrangement": MaterialOutsourcingType.NO,
                "address": "444 Marketing Plaza",
                "city": "Chicago",
                "state": "Illinois",
                "zip_code": "60601",
                "email": "contact@digitalmarketing.com",
                "phone": "+1-312-5551101"
            },
            {
                "vendor_name": "Financial Advisory Services",
                "vendor_contact_person": "Liam O'Brien",
                "vendor_country": "Canada",
                "bank_customer": BankCustomerType.ORCO_BANK,
                "cif": "901234",
                "material_outsourcing_arrangement": MaterialOutsourcingType.YES,
                "address": "555 Finance Street",
                "city": "Vancouver",
                "state": "British Columbia",
                "zip_code": "V6B1H8",
                "email": "advisory@financialservices.ca",
                "phone": "+1-604-5551201"
            },
            {
                "vendor_name": "HR Management Solutions",
                "vendor_contact_person": "Maria Santos",
                "vendor_country": "Aruba",
                "bank_customer": BankCustomerType.ARUBA_BANK,
                "cif": "012345",
                "material_outsourcing_arrangement": MaterialOutsourcingType.NO,
                "address": "666 HR Boulevard",
                "city": "",
                "state": "",
                "zip_code": "",
                "email": "hr@management.aw",
                "phone": "297-5551301"
            },
            {
                "vendor_name": "Legal Compliance Corp",
                "vendor_contact_person": "Nathan White",
                "vendor_country": "United States",
                "bank_customer": BankCustomerType.ARUBA_BANK,
                "cif": "123450",
                "material_outsourcing_arrangement": MaterialOutsourcingType.YES,
                "address": "777 Legal Way",
                "city": "Washington",
                "state": "DC",
                "zip_code": "20001",
                "email": "compliance@legal.com",
                "phone": "+1-202-5551401"
            },
            {
                "vendor_name": "Training and Development Inc",
                "vendor_contact_person": "Olivia Martinez",
                "vendor_country": "Mexico",
                "bank_customer": BankCustomerType.NONE,
                "cif": None,
                "material_outsourcing_arrangement": MaterialOutsourcingType.NO,
                "address": "888 Training Center",
                "city": "Guadalajara",
                "state": "Jalisco",
                "zip_code": "44100",
                "email": "training@development.mx",
                "phone": "+52-33-5551501"
            },
            {
                "vendor_name": "Equipment Leasing Partners",
                "vendor_contact_person": "Paul Johnson",
                "vendor_country": "United States",
                "bank_customer": BankCustomerType.ARUBA_BANK,
                "cif": "234501",
                "material_outsourcing_arrangement": MaterialOutsourcingType.YES,
                "address": "999 Lease Lane",
                "city": "Denver",
                "state": "Colorado",
                "zip_code": "80202",
                "email": "leasing@equipment.com",
                "phone": "+1-303-5551601"
            },
            {
                "vendor_name": "Customer Support Services",
                "vendor_contact_person": "Quinn Davis",
                "vendor_country": "Netherlands",
                "bank_customer": BankCustomerType.NONE,
                "cif": None,
                "material_outsourcing_arrangement": MaterialOutsourcingType.NO,
                "address": "101 Support Avenue",
                "city": "Rotterdam",
                "state": "South Holland",
                "zip_code": "3011",
                "email": "support@customer.nl",
                "phone": "+31-10-5551701"
            },
            {
                "vendor_name": "Telecommunications Provider",
                "vendor_contact_person": "Rachel Green",
                "vendor_country": "Curacao",
                "bank_customer": BankCustomerType.ORCO_BANK,
                "cif": "345012",
                "material_outsourcing_arrangement": MaterialOutsourcingType.YES,
                "address": "202 Telecom Road",
                "city": "",
                "state": "",
                "zip_code": "",
                "email": "info@telecom.cw",
                "phone": "+599-9-5551801"
            },
            {
                "vendor_name": "Office Supplies Distribution",
                "vendor_contact_person": "Steve Miller",
                "vendor_country": "United States",
                "bank_customer": BankCustomerType.ARUBA_BANK,
                "cif": "456123",
                "material_outsourcing_arrangement": MaterialOutsourcingType.NO,
                "address": "303 Supply Street",
                "city": "Seattle",
                "state": "Washington",
                "zip_code": "98101",
                "email": "orders@officesupplies.com",
                "phone": "+1-206-5551901"
            },
            {
                "vendor_name": "Facilities Management Group",
                "vendor_contact_person": "Tina Brown",
                "vendor_country": "Bonaire",
                "bank_customer": BankCustomerType.NONE,
                "cif": None,
                "material_outsourcing_arrangement": MaterialOutsourcingType.YES,
                "address": "404 Facilities Drive",
                "city": "",
                "state": "",
                "zip_code": "",
                "email": "facilities@management.bq",
                "phone": "+599-7-5552001"
            }
        ]
        
        vendors = []
        
        if vendors_created:
            print("Creating 20 vendors...\n")
            
            for i, vendor_data in enumerate(vendors_data, 1):
                # Determine bank type for vendor ID generation
                if vendor_data["bank_customer"] == BankCustomerType.ARUBA_BANK:
                    vendor_id = f"AB{i}"
                elif vendor_data["bank_customer"] == BankCustomerType.ORCO_BANK:
                    vendor_id = f"OB{i}"
                else:
                    vendor_id = f"AB{i}"  # Default
                
                # Calculate due diligence dates
                last_dd_date = datetime.now(timezone.utc) - timedelta(days=180)  # 6 months ago
                if vendor_data["material_outsourcing_arrangement"] == MaterialOutsourcingType.YES:
                    next_dd_date = last_dd_date + relativedelta(years=1)
                else:
                    next_dd_date = last_dd_date + relativedelta(years=3)
                
                # Randomly assign status (60% Active, 40% Inactive for realistic distribution)
                vendor_status = random.choices(
                    [VendorStatusType.ACTIVE, VendorStatusType.INACTIVE],
                    weights=[60, 40],
                    k=1
                )[0]
                
                # Create vendor
                vendor = Vendor(
                    vendor_id=vendor_id,
                    vendor_name=vendor_data["vendor_name"],
                    vendor_contact_person=vendor_data["vendor_contact_person"],
                    vendor_country=vendor_data["vendor_country"],
                    material_outsourcing_arrangement=vendor_data["material_outsourcing_arrangement"],
                    bank_customer=vendor_data["bank_customer"],
                    cif=vendor_data.get("cif"),
                    due_diligence_required=DueDiligenceRequiredType.YES,
                    last_due_diligence_date=last_dd_date,
                    next_required_due_diligence_date=next_dd_date,
                    next_required_due_diligence_alert_frequency=AlertFrequencyType.THIRTY_DAYS,
                    status=vendor_status,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                
                db.add(vendor)
                db.flush()
                
                # Create address
                address = VendorAddress(
                    vendor_id=vendor.id,
                    address=vendor_data["address"],
                    city=vendor_data.get("city"),
                    state=vendor_data.get("state"),
                    zip_code=vendor_data.get("zip_code"),
                    is_primary=True,
                    created_at=datetime.now(timezone.utc)
                )
                db.add(address)
                
                # Create email
                email = VendorEmail(
                    vendor_id=vendor.id,
                    email=vendor_data["email"],
                    is_primary=True,
                    created_at=datetime.now(timezone.utc)
                )
                db.add(email)
                
                # Create phone
                phone = VendorPhone(
                    vendor_id=vendor.id,
                    area_code="+1",
                    phone_number=vendor_data["phone"],
                    is_primary=True,
                    created_at=datetime.now(timezone.utc)
                )
                db.add(phone)
                
                # Create vendor documents (Due Diligence and NDA)
                dd_path, dd_size = save_vendor_document(
                    vendor,
                    DocumentType.DUE_DILIGENCE,
                    f"{vendor_data['vendor_name']} Due Diligence",
                    last_dd_date
                )
                
                dd_doc = VendorDocument(
                    vendor_id=vendor.id,
                    document_type=DocumentType.DUE_DILIGENCE,
                    file_name="due_diligence.pdf",
                    custom_document_name=f"{vendor_data['vendor_name']} Due Diligence",
                    document_signed_date=last_dd_date,
                    file_path=dd_path,
                    file_size=dd_size,
                    content_type="application/pdf",
                    created_at=datetime.now(timezone.utc)
                )
                db.add(dd_doc)
                
                nda_path, nda_size = save_vendor_document(
                    vendor,
                    DocumentType.NON_DISCLOSURE_AGREEMENT,
                    f"{vendor_data['vendor_name']} NDA",
                    last_dd_date
                )
                
                nda_doc = VendorDocument(
                    vendor_id=vendor.id,
                    document_type=DocumentType.NON_DISCLOSURE_AGREEMENT,
                    file_name="nda.pdf",
                    custom_document_name=f"{vendor_data['vendor_name']} NDA",
                    document_signed_date=last_dd_date,
                    file_path=nda_path,
                    file_size=nda_size,
                    content_type="application/pdf",
                    created_at=datetime.now(timezone.utc)
                )
                db.add(nda_doc)
                
                vendors.append(vendor)
                print(f"  ✓ Created vendor: {vendor.vendor_id} - {vendor.vendor_name}")
            
            db.commit()
            print(f"\n✅ Successfully seeded {len(vendors)} vendors!\n")
        else:
            # Load existing vendors
            vendors = db.query(Vendor).limit(20).all()
            print(f"✓ Using {len(vendors)} existing vendors\n")
        
        # Create 20 contracts (doubled from 10)
        print("Creating 20 contracts...\n")
        
        contracts_data = [
            {
                "description": "IT Infrastructure Support Agreement",
                "contract_type": ContractType.SERVICE_AGREEMENT,
                "department": DepartmentType.IT,
                "amount": 50000.00,
                "currency": CurrencyType.USD,
                "start_offset_days": -30,
                "duration_days": 365
            },
            {
                "description": "Annual Software Maintenance",
                "contract_type": ContractType.MAINTENANCE_CONTRACT,
                "department": DepartmentType.IT,
                "amount": 25000.00,
                "currency": CurrencyType.AWG,
                "start_offset_days": -60,
                "duration_days": 365
            },
            {
                "description": "Cloud Services License",
                "contract_type": ContractType.SOFTWARE_LICENSE,
                "department": DepartmentType.IT,
                "amount": 75000.00,
                "currency": CurrencyType.USD,
                "start_offset_days": 0,
                "duration_days": 730
            },
            {
                "description": "Security Audit Consulting",
                "contract_type": ContractType.CONSULTING_AGREEMENT,
                "department": DepartmentType.RISK_MANAGEMENT,
                "amount": 30000.00,
                "currency": CurrencyType.EUR,
                "start_offset_days": -90,
                "duration_days": 180
            },
            {
                "description": "Data Center Hosting Services",
                "contract_type": ContractType.SERVICE_AGREEMENT,
                "department": DepartmentType.IT,
                "amount": 120000.00,
                "currency": CurrencyType.USD,
                "start_offset_days": -180,
                "duration_days": 1095
            },
            {
                "description": "Business Strategy Consulting",
                "contract_type": ContractType.CONSULTING_AGREEMENT,
                "department": DepartmentType.OPERATIONS,
                "amount": 45000.00,
                "currency": CurrencyType.USD,
                "start_offset_days": -45,
                "duration_days": 365
            },
            {
                "description": "Custom Software Development",
                "contract_type": ContractType.SERVICE_AGREEMENT,
                "department": DepartmentType.IT,
                "amount": 85000.00,
                "currency": CurrencyType.AWG,
                "start_offset_days": -120,
                "duration_days": 540
            },
            {
                "description": "Network Equipment Support",
                "contract_type": ContractType.SUPPORT_CONTRACT,
                "department": DepartmentType.IT,
                "amount": 35000.00,
                "currency": CurrencyType.USD,
                "start_offset_days": -15,
                "duration_days": 365
            },
            {
                "description": "Analytics Platform License",
                "contract_type": ContractType.SOFTWARE_LICENSE,
                "department": DepartmentType.FINANCE,
                "amount": 40000.00,
                "currency": CurrencyType.USD,
                "start_offset_days": 0,
                "duration_days": 365
            },
            {
                "description": "Enterprise System Integration",
                "contract_type": ContractType.OUTSOURCING_AGREEMENT,
                "department": DepartmentType.IT,
                "amount": 95000.00,
                "currency": CurrencyType.USD,
                "start_offset_days": -200,
                "duration_days": 1095
            },
            {
                "description": "Marketing Campaign Services",
                "contract_type": ContractType.SERVICE_AGREEMENT,
                "department": DepartmentType.MARKETING,
                "amount": 32000.00,
                "currency": CurrencyType.USD,
                "start_offset_days": -300,
                "duration_days": 360  # Expiring soon
            },
            {
                "description": "Financial Planning Advisory",
                "contract_type": ContractType.CONSULTING_AGREEMENT,
                "department": DepartmentType.FINANCE,
                "amount": 55000.00,
                "currency": CurrencyType.AWG,
                "start_offset_days": -280,
                "duration_days": 330  # Expiring within 90 days
            },
            {
                "description": "Payroll Management System",
                "contract_type": ContractType.SOFTWARE_LICENSE,
                "department": DepartmentType.HUMAN_RESOURCES,
                "amount": 28000.00,
                "currency": CurrencyType.USD,
                "start_offset_days": -20,
                "duration_days": 365
            },
            {
                "description": "Legal Document Review",
                "contract_type": ContractType.CONSULTING_AGREEMENT,
                "department": DepartmentType.LEGAL,
                "amount": 42000.00,
                "currency": CurrencyType.USD,
                "start_offset_days": -310,
                "duration_days": 365  # Expiring within 90 days
            },
            {
                "description": "Employee Training Program",
                "contract_type": ContractType.SERVICE_AGREEMENT,
                "department": DepartmentType.HUMAN_RESOURCES,
                "amount": 18000.00,
                "currency": CurrencyType.AWG,
                "start_offset_days": -250,
                "duration_days": 365
            },
            {
                "description": "Equipment Rental Agreement",
                "contract_type": ContractType.LEASE_AGREEMENT,
                "department": DepartmentType.OPERATIONS,
                "amount": 65000.00,
                "currency": CurrencyType.USD,
                "start_offset_days": -100,
                "duration_days": 730
            },
            {
                "description": "Call Center Support Services",
                "contract_type": ContractType.SUPPORT_CONTRACT,
                "department": DepartmentType.CUSTOMER_SERVICE,
                "amount": 38000.00,
                "currency": CurrencyType.USD,
                "start_offset_days": -320,
                "duration_days": 380  # Expiring within 90 days
            },
            {
                "description": "Mobile Network Services",
                "contract_type": ContractType.SERVICE_AGREEMENT,
                "department": DepartmentType.IT,
                "amount": 22000.00,
                "currency": CurrencyType.AWG,
                "start_offset_days": -290,
                "duration_days": 350  # Expiring within 90 days
            },
            {
                "description": "Office Supplies Annual Contract",
                "contract_type": ContractType.PURCHASE_AGREEMENT,
                "department": DepartmentType.OPERATIONS,
                "amount": 15000.00,
                "currency": CurrencyType.USD,
                "start_offset_days": -5,
                "duration_days": 365
            },
            {
                "description": "Building Maintenance Services",
                "contract_type": ContractType.MAINTENANCE_CONTRACT,
                "department": DepartmentType.OPERATIONS,
                "amount": 48000.00,
                "currency": CurrencyType.USD,
                "start_offset_days": -305,
                "duration_days": 365  # Expiring within 90 days
            }
        ]
        
        for i, contract_data in enumerate(contracts_data):
            vendor = vendors[i % len(vendors)]  # Distribute contracts across vendors
            
            # Calculate dates
            start_date = date.today() + timedelta(days=contract_data["start_offset_days"])
            end_date = start_date + timedelta(days=contract_data["duration_days"])
            
            # Determine contract status
            if end_date < date.today():
                status = ContractStatusType.EXPIRED
            elif start_date > date.today():
                status = ContractStatusType.ACTIVE
            else:
                status = ContractStatusType.ACTIVE
            
            # Create contract
            contract_id = f"CT{i+1}"
            contract = Contract(
                contract_id=contract_id,
                vendor_id=vendor.id,
                contract_description=contract_data["description"],
                contract_type=contract_data["contract_type"],
                start_date=start_date,
                end_date=end_date,
                automatic_renewal=AutomaticRenewalType.YES if i % 2 == 0 else AutomaticRenewalType.NO,
                renewal_period=RenewalPeriodType.ONE_YEAR if i % 2 == 0 else None,
                department=contract_data["department"],
                contract_amount=contract_data["amount"],
                contract_currency=contract_data["currency"],
                payment_method=PaymentMethodType.INVOICE if i % 2 == 0 else PaymentMethodType.STANDING_ORDER,
                termination_notice_period=NoticePeriodType.THIRTY_DAYS,
                expiration_notice_frequency=ExpirationNoticePeriodType.THIRTY_DAYS,
                contract_owner_id=users[i % len(users)].id,
                contract_owner_backup_id=users[(i+1) % len(users)].id,
                contract_owner_manager_id=users[(i+2) % len(users)].id,
                status=status,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            db.add(contract)
            db.flush()
            
            # Create contract document for some contracts (every other contract gets a document)
            # This creates a mix: some with documents, some without (for testing pending_contracts page)
            if i % 2 == 0:
                doc_path, doc_size = save_contract_document(
                    contract,
                    f"{contract_data['description']} - Signed",
                    start_date
                )
                
                contract_doc = ContractDocument(
                    contract_id=contract.id,
                    file_name="contract.pdf",
                    custom_document_name=f"{contract_data['description']} - Signed",
                    document_signed_date=start_date,
                    file_path=doc_path,
                    file_size=doc_size,
                    content_type="application/pdf",
                    created_at=datetime.now(timezone.utc)
                )
                db.add(contract_doc)
                print(f"  ✓ Created contract: {contract.contract_id} - {contract.contract_description} ({vendor.vendor_name}) [WITH DOCUMENT]")
            else:
                print(f"  ✓ Created contract: {contract.contract_id} - {contract.contract_description} ({vendor.vendor_name}) [NO DOCUMENT]")
        
        db.commit()
        print(f"\n✅ Successfully seeded 20 contracts!")
        
        # Count contracts with and without documents
        contracts_with_docs = sum(1 for i in range(len(contracts_data)) if i % 2 == 0)
        contracts_without_docs = len(contracts_data) - contracts_with_docs
        
        # Count contracts expiring within 90 days
        contracts_expiring_soon = 0
        for i, contract_data in enumerate(contracts_data):
            start_date = date.today() + timedelta(days=contract_data["start_offset_days"])
            end_date = start_date + timedelta(days=contract_data["duration_days"])
            if date.today() <= end_date <= date.today() + timedelta(days=90):
                contracts_expiring_soon += 1
        
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        print(f"Vendors: {len(vendors)}")
        print(f"Contracts: {len(contracts_data)}")
        print(f"  - With documents: {contracts_with_docs}")
        print(f"  - Without documents: {contracts_without_docs} (will appear in Pending Documents)")
        print(f"  - Expiring within 90 days: {contracts_expiring_soon} (will appear in Pending Reviews)")
        print(f"Users available: {len(users)}")
        print("="*70)
        
    except Exception as e:
        print(f"❌ Error seeding vendors and contracts: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_vendors_and_contracts()

