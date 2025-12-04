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
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import os
import uuid


def create_dummy_pdf(output_path):
    """
    Create a minimal valid PDF file for testing
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
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
    
    with open(output_path, 'wb') as f:
        f.write(pdf_content)
    
    return output_path


def save_vendor_document(vendor, document_type, doc_name, signed_date):
    """
    Save a vendor document by creating a dummy PDF
    """
    upload_dir = os.path.join("uploads", "vendors", vendor.vendor_id)
    os.makedirs(upload_dir, exist_ok=True)
    
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
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename
    unique_filename = f"contract_{uuid.uuid4()}.pdf"
    file_path = os.path.join(upload_dir, unique_filename)
    
    # Create dummy PDF
    create_dummy_pdf(file_path)
    
    # Get file size
    file_size = os.path.getsize(file_path)
    
    return file_path, file_size


def seed_vendors_and_contracts():
    db = SessionLocal()
    
    try:
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
        
        # Create 10 vendors
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
            }
        ]
        
        vendors = []
        
        if vendors_created:
            print("Creating 10 vendors...\n")
            
            for i, vendor_data in enumerate(vendors_data, 1):
                # Determine bank type for vendor ID generation
                if vendor_data["bank_customer"] == BankCustomerType.ARUBA_BANK:
                    vendor_id = f"AB{i}"
                elif vendor_data["bank_customer"] == BankCustomerType.ORCO_BANK:
                    vendor_id = f"OB{i}"
                else:
                    vendor_id = f"AB{i}"  # Default
                
                # Calculate due diligence dates
                last_dd_date = datetime.utcnow() - timedelta(days=180)  # 6 months ago
                if vendor_data["material_outsourcing_arrangement"] == MaterialOutsourcingType.YES:
                    next_dd_date = last_dd_date + relativedelta(years=1)
                else:
                    next_dd_date = last_dd_date + relativedelta(years=3)
                
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
                    status=VendorStatusType.ACTIVE,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
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
                    created_at=datetime.utcnow()
                )
                db.add(address)
                
                # Create email
                email = VendorEmail(
                    vendor_id=vendor.id,
                    email=vendor_data["email"],
                    is_primary=True,
                    created_at=datetime.utcnow()
                )
                db.add(email)
                
                # Create phone
                phone = VendorPhone(
                    vendor_id=vendor.id,
                    area_code="+1",
                    phone_number=vendor_data["phone"],
                    is_primary=True,
                    created_at=datetime.utcnow()
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
                    created_at=datetime.utcnow()
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
                    created_at=datetime.utcnow()
                )
                db.add(nda_doc)
                
                vendors.append(vendor)
                print(f"  ✓ Created vendor: {vendor.vendor_id} - {vendor.vendor_name}")
            
            db.commit()
            print(f"\n✅ Successfully seeded {len(vendors)} vendors!\n")
        else:
            # Load existing vendors
            vendors = db.query(Vendor).limit(10).all()
            print(f"✓ Using {len(vendors)} existing vendors\n")
        
        # Create 10 contracts
        print("Creating 10 contracts...\n")
        
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
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(contract)
            db.flush()
            
            # Create contract document
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
                created_at=datetime.utcnow()
            )
            db.add(contract_doc)
            
            print(f"  ✓ Created contract: {contract.contract_id} - {contract.contract_description} ({vendor.vendor_name})")
        
        db.commit()
        print(f"\n✅ Successfully seeded 10 contracts!")
        
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"Vendors: {len(vendors)}")
        print(f"Contracts: {len(contracts_data)}")
        print(f"Users available: {len(users)}")
        print("="*60)
        
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

