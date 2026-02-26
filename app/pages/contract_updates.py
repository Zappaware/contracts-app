from datetime import datetime, timedelta, date
import asyncio
import logging
from nicegui import ui, app, run
import io
import re
import base64
import httpx
from app.utils.vendor_lookup import get_vendor_id_by_name
from app.utils.navigation import get_dashboard_url
from app.db.database import SessionLocal
from sqlalchemy.orm import joinedload
from app.models.contract import (
    ContractUpdate,
    ContractUpdateStatus,
    Contract,
    ContractStatusType,
    ContractTerminationType,
    User,
    UserRole,
)
from app.models.vendor import Vendor
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

log = logging.getLogger(__name__)


def _complete_returned_update_blocking(
    update_id: int | None,
    contract_db_id: int,
    current_user_id,
    decision: str,
    end_val: str | None,
    term_doc_name: str,
    term_doc_date: str,
    term_doc_file_content: bytes | None,
    term_doc_file_name: str,
    manager_comments: str,
    has_document_final: bool,
) -> tuple[bool, str | None]:
    """Run in background: upload termination doc (if any) and set ContractUpdate to PENDING_REVIEW. Returns (success, error_message)."""
    log.info("_complete_returned_update_blocking: update_id=%s contract_db_id=%s decision=%s", update_id, contract_db_id, decision)
    try:
        if decision == "Terminate" and term_doc_file_content:
            with httpx.Client(timeout=90.0) as client:
                r = client.post(
                    f"http://localhost:8000/api/v1/contracts/{contract_db_id}/termination-documents",
                    data={"document_name": term_doc_name.strip(), "document_date": term_doc_date.strip()},
                    files={"file": (term_doc_file_name or "document.pdf", term_doc_file_content, "application/pdf")},
                )
            if r.status_code not in (200, 201):
                try:
                    body = r.json()
                    detail = body.get("detail", "Failed to store termination document")
                    if isinstance(detail, list):
                        detail = "; ".join(str(x.get("msg", x)) for x in detail) if detail else "Request failed"
                    return (False, str(detail))
                except Exception:
                    return (False, (r.text or f"Request failed (HTTP {r.status_code})"))
        db = SessionLocal()
        try:
            upd = db.query(ContractUpdate).filter(ContractUpdate.id == (update_id or 0)).first()
            if not upd and contract_db_id:
                upd = (
                    db.query(ContractUpdate)
                    .filter(ContractUpdate.contract_id == contract_db_id)
                    .order_by(ContractUpdate.created_at.desc())
                    .first()
                )
            if not upd:
                return (False, "Contract update not found")
            upd.status = ContractUpdateStatus.PENDING_REVIEW
            upd.response_provided_by_user_id = current_user_id
            upd.response_date = datetime.utcnow()
            upd.decision_comments = manager_comments or ""
            upd.decision = "Extend" if decision == "Renew" else decision
            upd.has_document = has_document_final
            if decision == "Renew" and end_val:
                try:
                    upd.initial_expiration_date = datetime.strptime(end_val.replace("/", "-")[:10], "%Y-%m-%d").date()
                except Exception:
                    pass
            upd.updated_at = datetime.utcnow()
            db.commit()
            log.info("_complete_returned_update_blocking: success, status set to PENDING_REVIEW")
            return (True, None)
        finally:
            db.close()
    except Exception as e:
        return (False, str(e))


def contract_updates():
    # Current user (for My Role column)
    current_user_id = None
    current_user_role = None
    try:
        current_username = app.storage.user.get("username", None) if app.storage.user else None
        if current_username:
            db_user = SessionLocal()
            try:
                u = db_user.query(User).filter(User.email == current_username).first()
                if not u:
                    u = db_user.query(User).filter(User.email.ilike(f"%{current_username}%")).first()
                if u:
                    current_user_id = u.id
                    current_user_role = u.role.value if hasattr(u.role, "value") else str(u.role)
            finally:
                db_user.close()
    except Exception as e:
        print(f"Error resolving current user for contract_updates: {e}")

    # Navigation
    with ui.row().classes("max-w-6xl mx-auto mt-4"):
        with ui.link(target=get_dashboard_url()).classes('no-underline'):
            ui.button("Back to Dashboard", icon="arrow_back").props('flat color=primary')
    
    # Global variables for table and data
    contracts_table = None
    contract_rows = []
    
    # Mock data fallback (for testing or if API unavailable)
    def get_mock_contract_updates():
        """
        Fallback mock data if API is unavailable.
        """
        today = datetime.now()
        
        mock_contracts = [
            {
                "contract_id": "CTR-2024-001",
                "vendor_name": "Acme Corp",
                "contract_type": "Service Agreement",
                "description": "IT Support Services",
                "expiration_date": today + timedelta(days=30),
                "manager": "William Defoe",
                "role": "owned",
                "response_provided_by": "William Defoe",
                "response_date": today - timedelta(days=2),
                "has_document": True,
                "status": "returned",
                "previous_response": None,
                "returned_reason": "Contract requires additional documentation and signature verification.",
                "admin_comments": "Please provide the complete signed contract document and verify vendor contact information.",
                "initial_description": "IT Support Services",
                "initial_vendor": "Acme Corp",
                "initial_type": "Service Agreement",
                "initial_expiration": today + timedelta(days=30)
            },
            {
                "contract_id": "CTR-2024-012",
                "vendor_name": "Beta Technologies",
                "contract_type": "Software License",
                "description": "Enterprise Software Licensing",
                "expiration_date": today + timedelta(days=45),
                "manager": "John Doe",
                "role": "backup",
                "response_provided_by": "John Doe",
                "response_date": today - timedelta(days=1),
                "has_document": True,
                "status": "updated",
                "previous_response": {
                    "date": today - timedelta(days=10),
                    "response": "Initial response provided with all required documents.",
                    "has_document": True
                },
                "returned_reason": "Missing signature on page 3",
                "returned_date": today - timedelta(days=8),
                "correction_date": today - timedelta(days=1),
                "admin_comments": "The contract document is missing the authorized signature on page 3. Please obtain the signature and resubmit.",
                "initial_description": "Enterprise Software Licensing",
                "initial_vendor": "Beta Technologies",
                "initial_type": "Software License",
                "initial_expiration": today + timedelta(days=45)
            },
            {
                "contract_id": "CTR-2024-023",
                "vendor_name": "Gamma Consulting",
                "contract_type": "Consulting",
                "description": "Business Process Optimization",
                "expiration_date": today + timedelta(days=60),
                "manager": "William Defoe",
                "role": "owned",
                "response_provided_by": "William Defoe",
                "response_date": today - timedelta(days=3),
                "has_document": False,
                "status": "updated",
                "previous_response": None,
                "returned_reason": None
            },
            {
                "contract_id": "CTR-2024-034",
                "vendor_name": "Delta Logistics",
                "contract_type": "Transportation",
                "description": "Freight and Delivery Services",
                "expiration_date": today + timedelta(days=15),
                "manager": "John Doe",
                "role": "backup",
                "response_provided_by": "John Doe",
                "response_date": today - timedelta(days=5),
                "has_document": True,
                "status": "returned",
                "previous_response": {
                    "date": today - timedelta(days=12),
                    "response": "Original response submitted with contract details.",
                    "has_document": True
                },
                "returned_reason": "Incomplete vendor information",
                "returned_date": today - timedelta(days=10),
                "correction_date": today - timedelta(days=5),
                "admin_comments": "Vendor contact person and address information is incomplete. Please update with complete vendor details.",
                "initial_description": "Freight and Delivery Services",
                "initial_vendor": "Delta Logistics",
                "initial_type": "Transportation",
                "initial_expiration": today + timedelta(days=15)
            },
            {
                "contract_id": "CTR-2023-089",
                "vendor_name": "Epsilon Security",
                "contract_type": "Security Services",
                "description": "Building Security and Monitoring",
                "expiration_date": today + timedelta(days=90),
                "manager": "William Defoe",
                "role": "owned",
                "response_provided_by": "William Defoe",
                "response_date": today - timedelta(days=4),
                "has_document": True,
                "status": "returned",
                "previous_response": None,
                "returned_reason": "Contract expiration date needs verification against vendor agreement.",
                "admin_comments": "The expiration date in the system does not match the date on the signed contract document. Please verify and update.",
                "initial_description": "Building Security and Monitoring",
                "initial_vendor": "Epsilon Security",
                "initial_type": "Security Services",
                "initial_expiration": today + timedelta(days=90)
            },
            {
                "contract_id": "CTR-2024-045",
                "vendor_name": "Zeta Solutions",
                "contract_type": "Maintenance",
                "description": "Equipment Maintenance Contract",
                "expiration_date": today + timedelta(days=75),
                "manager": "John Doe",
                "role": "backup",
                "response_provided_by": "John Doe",
                "response_date": today - timedelta(days=2),
                "has_document": False,
                "status": "updated",
                "previous_response": {
                    "date": today - timedelta(days=15),
                    "response": "First response with maintenance schedule.",
                    "has_document": False
                },
                "returned_reason": "Required maintenance schedule document missing",
                "returned_date": today - timedelta(days=12),
                "correction_date": today - timedelta(days=2)
            },
            {
                "contract_id": "CTR-2024-056",
                "vendor_name": "Eta Services",
                "contract_type": "Cleaning Services",
                "description": "Office Cleaning and Janitorial",
                "expiration_date": today + timedelta(days=25),
                "manager": "William Defoe",
                "role": "owned",
                "response_provided_by": "William Defoe",
                "response_date": today - timedelta(days=1),
                "has_document": True,
                "status": "returned",
                "previous_response": None,
                "returned_reason": "Contract type classification needs correction.",
                "admin_comments": "This contract should be classified as 'Service Agreement' rather than 'Cleaning Services'. Please update the contract type.",
                "initial_description": "Office Cleaning and Janitorial",
                "initial_vendor": "Eta Services",
                "initial_type": "Cleaning Services",
                "initial_expiration": today + timedelta(days=25)
            },
            {
                "contract_id": "CTR-2024-067",
                "vendor_name": "Theta Communications",
                "contract_type": "Telecommunications",
                "description": "Internet and Phone Services",
                "expiration_date": today + timedelta(days=50),
                "manager": "John Doe",
                "role": "backup",
                "response_provided_by": "John Doe",
                "response_date": today - timedelta(days=3),
                "has_document": True,
                "status": "updated",
                "previous_response": {
                    "date": today - timedelta(days=14),
                    "response": "Initial telecommunications contract response.",
                    "has_document": True
                },
                "returned_reason": None,
                "returned_date": None,
                "correction_date": today - timedelta(days=3)
            },
            {
                "contract_id": "CTR-2024-078",
                "vendor_name": "Iota Manufacturing",
                "contract_type": "Supply Agreement",
                "description": "Raw Materials Supply",
                "expiration_date": today + timedelta(days=35),
                "manager": "William Defoe",
                "role": "owned",
                "response_provided_by": "William Defoe",
                "response_date": today - timedelta(days=2),
                "has_document": True,
                "status": "returned",
                "previous_response": None,
                "returned_reason": "Vendor information and contract terms need review.",
                "admin_comments": "Please verify vendor credentials and ensure all contract terms are properly documented before resubmission.",
                "initial_description": "Raw Materials Supply",
                "initial_vendor": "Iota Manufacturing",
                "initial_type": "Supply Agreement",
                "initial_expiration": today + timedelta(days=35)
            },
            {
                "contract_id": "CTR-2024-089",
                "vendor_name": "Kappa Services",
                "contract_type": "Maintenance",
                "description": "HVAC Maintenance Services",
                "expiration_date": today + timedelta(days=20),
                "manager": "John Doe",
                "role": "backup",
                "response_provided_by": "John Doe",
                "response_date": today - timedelta(days=4),
                "has_document": False,
                "status": "updated",
                "previous_response": {
                    "date": today - timedelta(days=16),
                    "response": "HVAC maintenance contract response.",
                    "has_document": False
                },
                "returned_reason": None,
                "returned_date": None,
                "correction_date": today - timedelta(days=4)
            },
        ]
        
        rows = []
        for contract in mock_contracts:
            exp_date = contract["expiration_date"]
            
            # Look up vendor_id from vendor_name
            vendor_id = get_vendor_id_by_name(contract["vendor_name"])
            
            # My Role for display: map owned/backup to ticket labels; mock may show Contract Manager, Backup, Owner, N/A
            role_val = contract.get("role", "owned")
            if role_val == "owned":
                my_role_mock = "Contract Manager"
            elif role_val == "backup":
                my_role_mock = "Backup"
            else:
                my_role_mock = "N/A"
            row_data = {
                "contract_id": contract["contract_id"],
                "vendor_name": contract["vendor_name"],
                "vendor_id": vendor_id,  # Add vendor_id for routing
                "contract_type": contract["contract_type"],
                "description": contract["description"],
                "expiration_date": exp_date.strftime("%Y-%m-%d"),
                "expiration_timestamp": exp_date.timestamp(),  # For sorting
                "manager": contract["manager"],
                "my_role": my_role_mock,
                "role": contract["role"],
                "response_provided_by": contract["response_provided_by"],
                "response_date": contract["response_date"].strftime("%Y-%m-%d"),
                "has_document": contract["has_document"],
                "status": contract["status"],  # "pending_approval" or "returned"
                "previous_response": contract.get("previous_response"),
                "returned_reason": contract.get("returned_reason"),
                "returned_date": contract.get("returned_date").strftime("%Y-%m-%d") if contract.get("returned_date") else None,
                "correction_date": contract.get("correction_date").strftime("%Y-%m-%d") if contract.get("correction_date") else None,
                "admin_comments": contract.get("admin_comments", ""),
                "initial_description": contract.get("initial_description", contract.get("description", "")),
                "initial_vendor": contract.get("initial_vendor", contract.get("vendor_name", "")),
                "initial_type": contract.get("initial_type", contract.get("contract_type", "")),
                "initial_expiration": contract.get("initial_expiration").strftime("%Y-%m-%d") if contract.get("initial_expiration") else contract.get("expiration_date", ""),
            }
            rows.append(row_data)
        
        return rows

    contract_columns = [
        {
            "name": "contract_id",
            "label": "Contract ID",
            "field": "contract_id",
            "align": "left",
            "sortable": True,
        },
        {
            "name": "vendor_name",
            "label": "Vendor Name",
            "field": "vendor_name",
            "align": "left",
            "sortable": True,
        },
        {
            "name": "contract_type",
            "label": "Contract Type",
            "field": "contract_type",
            "align": "left",
            "sortable": True,
        },
        {
            "name": "description",
            "label": "Contract Description",
            "field": "description",
            "align": "left",
        },
        {
            "name": "expiration_date",
            "label": "Expiration Date",
            "field": "expiration_date",
            "align": "left",
            "sortable": True,
            "sort-order": "ad",  # Ascending/Descending
        },
        {
            "name": "my_role",
            "label": "My Role",
            "field": "my_role",
            "align": "left",
            "sortable": True,
        },
        {
            "name": "status",
            "label": "Status",
            "field": "status",
            "align": "center",
            "sortable": True,
        },
    ]

    contract_columns_defaults = {
        "align": "left",
        "headerClasses": "bg-[#144c8e] text-white",
    }

    # Fetch contract updates from API (or use mock as fallback)
    contract_rows = []
    
    def reload_contract_updates():
        """Reload contract updates from database"""
        nonlocal contract_rows
        new_rows = load_data_sync()
        if new_rows:
            contract_rows = new_rows
            # Update filter options with new data
            vendor_options = ['All'] + sorted(list(set([row['vendor_name'] for row in contract_rows if row.get('vendor_name')])))
            type_options = ['All'] + sorted(list(set([row['contract_type'] for row in contract_rows if row.get('contract_type')])))
            vendor_filter.options = vendor_options
            type_filter.options = type_options
        else:
            # Fallback to mock data if database returns empty
            contract_rows = get_mock_contract_updates()
            # Update filter options with mock data
            vendor_options = ['All'] + sorted(list(set([row['vendor_name'] for row in contract_rows if row.get('vendor_name')])))
            type_options = ['All'] + sorted(list(set([row['contract_type'] for row in contract_rows if row.get('contract_type')])))
            vendor_filter.options = vendor_options
            type_filter.options = type_options
        if contracts_table:
            # Update contract_data_map for action handlers
            contract_data_map.clear()
            contract_data_map.update({row['contract_id']: row for row in contract_rows})
            apply_filters()
    
    # Fetch contract updates directly from database (like active_contracts.py)
    def load_data_sync():
        """
        Load contract updates directly from the database.
        This avoids HTTP requests and circular dependencies.
        """
        db = SessionLocal()
        try:
            # Use eager loading to prevent N+1 queries
            query = db.query(ContractUpdate).options(
                joinedload(ContractUpdate.contract).joinedload(Contract.vendor),
                joinedload(ContractUpdate.contract).joinedload(Contract.contract_owner),
                joinedload(ContractUpdate.response_provided_by)
            ).join(Contract)
            
            # Exclude completed updates - they are removed from the contract updates list
            updates = query.filter(ContractUpdate.status != ContractUpdateStatus.COMPLETED).order_by(ContractUpdate.created_at.desc()).all()
            
            print(f"Found {len(updates)} contract updates from database")
            
            if not updates:
                print("No contract updates found in database")
                return []
            
            rows = []
            for update in updates:
                contract = update.contract
                vendor = contract.vendor if contract.vendor else None
                
                # Get contract ID (string) and database ID (int)
                contract_id_str = contract.contract_id if contract else "Unknown"
                contract_db_id = contract.id if contract else None
                
                # Get vendor info
                vendor_name = vendor.vendor_name if vendor else "Unknown"
                vendor_id = vendor.id if vendor else None
                
                # Get contract type
                contract_type = contract.contract_type.value if contract and hasattr(contract.contract_type, 'value') else str(contract.contract_type) if contract else "Unknown"
                
                # Get description
                description = contract.contract_description if contract else "Unknown"
                
                # Format expiration date
                if contract and contract.end_date:
                    if isinstance(contract.end_date, date):
                        exp_date = contract.end_date
                        exp_date_str = exp_date.strftime("%Y-%m-%d")
                        exp_timestamp = datetime.combine(exp_date, datetime.min.time()).timestamp()
                    else:
                        exp_date_str = str(contract.end_date)
                        exp_timestamp = datetime.now().timestamp()
                else:
                    exp_date_str = "N/A"
                    exp_timestamp = 0
                
                # Manager name (kept for dialogs)
                manager_name = f"{contract.contract_owner.first_name} {contract.contract_owner.last_name}" if contract and contract.contract_owner else "Unknown"
                
                # My Role: for Contract Admin show the role of who took action; for others show logged-in user's role
                response_provided_by_user_id = update.response_provided_by_user_id if update else None
                if current_user_role == UserRole.CONTRACT_ADMIN.value:
                    # Admin view: show the role of the user who provided the response (Contract Manager, Backup, or Owner)
                    if contract and response_provided_by_user_id:
                        if contract.contract_owner_id == response_provided_by_user_id:
                            my_role = "Contract Manager"
                        elif contract.contract_owner_backup_id == response_provided_by_user_id:
                            my_role = "Backup"
                        elif contract.contract_owner_manager_id == response_provided_by_user_id:
                            my_role = "Owner"
                        else:
                            my_role = "N/A"
                    else:
                        # No response yet: show Contract Manager as primary role for the contract
                        my_role = "Contract Manager" if contract else "N/A"
                elif current_user_id and contract:
                    if contract.contract_owner_id == current_user_id:
                        my_role = "Contract Manager"
                    elif contract.contract_owner_backup_id == current_user_id:
                        my_role = "Backup"
                    elif contract.contract_owner_manager_id == current_user_id:
                        my_role = "Owner"
                    else:
                        my_role = "N/A"
                else:
                    my_role = "N/A"
                
                # Determine who provided the response
                response_provided_by = None
                role = "owned"
                if update.response_provided_by:
                    response_provided_by = f"{update.response_provided_by.first_name} {update.response_provided_by.last_name}"
                    if contract and contract.contract_owner_id == update.response_provided_by_user_id:
                        role = "owned"
                    elif contract and contract.contract_owner_backup_id == update.response_provided_by_user_id:
                        role = "backup"
                
                # Format response date
                response_date_str = None
                if update.response_date:
                    if isinstance(update.response_date, datetime):
                        response_date_str = update.response_date.strftime("%Y-%m-%d")
                    else:
                        response_date_str = str(update.response_date)
                
                # Format returned date
                returned_date_str = None
                if update.returned_date:
                    if isinstance(update.returned_date, datetime):
                        returned_date_str = update.returned_date.strftime("%Y-%m-%d")
                    else:
                        returned_date_str = str(update.returned_date)
                
                # Format correction date
                correction_date_str = None
                if update.correction_date:
                    if isinstance(update.correction_date, datetime):
                        correction_date_str = update.correction_date.strftime("%Y-%m-%d")
                    else:
                        correction_date_str = str(update.correction_date)
                
                # Get status value: backend value and display value (AC: "Review" for Admin, "Updated" for Manager/Backup/Owner when pending_review)
                status_raw = update.status.value if hasattr(update.status, 'value') else str(update.status)
                if status_raw == ContractUpdateStatus.PENDING_REVIEW.value:
                    status_value = "Review" if current_user_role == UserRole.CONTRACT_ADMIN.value else "Updated"
                else:
                    status_value = status_raw  # "returned", "updated", "completed"
                
                # Decision from Contract Manager/Backup/Owner (Renew/Terminate)
                decision_value = update.decision if update.decision else None
                decision_comments_value = update.decision_comments if update.decision_comments else ""

                row_data = {
                    "id": contract_db_id,  # Use contract DB ID for linking to contract-info page
                    "update_id": update.id,  # Keep update ID for API calls
                    "contract_id": contract_id_str,  # Contract ID string (e.g., "CT1")
                    "vendor_name": vendor_name,
                    "vendor_id": vendor_id,  # Vendor database ID for linking
                    "contract_type": contract_type,
                    "description": description,
                    "expiration_date": exp_date_str,
                    "expiration_timestamp": exp_timestamp,
                    "manager": manager_name,
                    "my_role": my_role,
                    "role": role,
                    "response_provided_by": response_provided_by,
                    "response_date": response_date_str,
                    "has_document": update.has_document if update.has_document else False,
                    "status": status_value,
                    "status_raw": status_raw,
                    "admin_comments": update.admin_comments,
                    "decision": decision_value,
                    "decision_comments": decision_comments_value,
                    "returned_reason": update.returned_reason,
                    "returned_date": returned_date_str,
                    "correction_date": correction_date_str,
                    "initial_description": update.initial_description if update.initial_description else description,
                    "initial_vendor": update.initial_vendor_name if update.initial_vendor_name else vendor_name,
                    "initial_type": update.initial_contract_type if update.initial_contract_type else contract_type,
                    "initial_expiration": update.initial_expiration_date.strftime("%Y-%m-%d") if update.initial_expiration_date else exp_date_str,
                    "previous_response": {
                        "date": returned_date_str,
                        "response": update.initial_description if update.initial_description else description,
                        "has_document": update.has_document if update.has_document else False
                    } if update.returned_date else None,
                }
                rows.append(row_data)
            
            print(f"Processed {len(rows)} contract update rows")
            return rows
            
        except Exception as e:
            error_msg = f"Error loading contract updates: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return []
        finally:
            db.close()
    
    # Start with empty data - will be loaded asynchronously
    contract_rows = []
    
    # Filter dropdowns
    owner_filter = None
    vendor_filter = None
    type_filter = None
    status_filter = None
    search_input = None
    loading_label = None
    
    # Main container
    with ui.element("div").classes("max-w-6xl mt-8 mx-auto w-full"):
        # Loading indicator
        loading_label = ui.label("Loading contract updates...").classes("text-lg text-gray-500 ml-4 mb-4")
        # Section header
        with ui.row().classes('items-center justify-between ml-4 mb-4 w-full'):
            with ui.row().classes('items-center gap-2'):
                ui.icon('update', color='primary').style('font-size: 32px')
                ui.label("Contract Updates").classes("text-h5 font-bold")
        
        # Tab system for All Updates vs Returned Contracts
        with ui.row().classes('ml-4 mb-4 w-full gap-2 border-b-2 border-gray-200 pb-2'):
            # Tab buttons
            all_tab_button = ui.button("All Contract Updates", icon="list", on_click=lambda: switch_tab('all')).props('flat').classes('tab-button')
            returned_tab_button = ui.button("Returned Contracts", icon="undo", on_click=lambda: switch_tab('returned')).props('flat color=negative').classes('tab-button')
        
        # Description row (dynamic based on tab)
        description_label = ui.label("Review responses provided by Contract Managers or Backups").classes(
            "text-sm text-gray-500 ml-4 mb-4"
        )
        
        # Filter section with dropdowns
        with ui.row().classes('w-full ml-4 mr-4 mb-4 gap-4 px-2 flex-wrap'):
            # My Role filter
            with ui.column().classes('flex-1 min-w-[200px]'):
                ui.label("Filter by My Role:").classes("text-sm font-medium mb-1")
                owner_filter = ui.select(
                    options=['All', 'Contract Manager', 'Backup', 'Owner', 'N/A'],
                    value='All',
                    on_change=lambda e: apply_filters()
                ).classes('w-full').props('outlined dense')
            
            # Vendor Name filter
            with ui.column().classes('flex-1 min-w-[200px]'):
                ui.label("Filter by Vendor Name:").classes("text-sm font-medium mb-1")
                vendor_options = ['All'] + sorted(list(set([row['vendor_name'] for row in contract_rows])))
                vendor_filter = ui.select(
                    options=vendor_options,
                    value='All',
                    on_change=lambda e: apply_filters()
                ).classes('w-full').props('outlined dense')
            
            # Contract Type filter
            with ui.column().classes('flex-1 min-w-[200px]'):
                ui.label("Filter by Contract Type:").classes("text-sm font-medium mb-1")
                type_options = ['All'] + sorted(list(set([row['contract_type'] for row in contract_rows])))
                type_filter = ui.select(
                    options=type_options,
                    value='All',
                    on_change=lambda e: apply_filters()
                ).classes('w-full').props('outlined dense')
            
            # Status filter
            with ui.column().classes('flex-1 min-w-[200px]'):
                ui.label("Filter by Status:").classes("text-sm font-medium mb-1")
                status_filter = ui.select(
                    options=['All', 'Returned', 'Updated', 'Review'],
                    value='All',
                    on_change=lambda e: apply_filters()
                ).classes('w-full').props('outlined dense')
        
        # Define filter function
        def apply_filters():
            # Show all contracts regardless of role
            base_rows = contract_rows
            
            # Apply My Role filter
            if owner_filter.value and owner_filter.value != 'All':
                base_rows = [row for row in base_rows if row.get('my_role') == owner_filter.value]
            
            # Apply vendor filter
            if vendor_filter.value and vendor_filter.value != 'All':
                base_rows = [row for row in base_rows if row['vendor_name'] == vendor_filter.value]
            
            # Apply type filter
            if type_filter.value and type_filter.value != 'All':
                base_rows = [row for row in base_rows if row['contract_type'] == type_filter.value]
            
            # Apply status filter (display values: returned, Updated, Review, completed)
            if status_filter.value and status_filter.value != 'All':
                if status_filter.value == 'Returned':
                    base_rows = [row for row in base_rows if row.get('status') == 'returned']
                elif status_filter.value == 'Updated':
                    base_rows = [row for row in base_rows if row.get('status') in ('updated', 'Updated')]
                elif status_filter.value == 'Review':
                    base_rows = [row for row in base_rows if row.get('status') == 'Review']
            
            # Apply search filter (including status)
            search_term = (search_input.value or "").lower()
            if search_term:
                base_rows = [
                    row for row in base_rows
                    if search_term in (row['contract_id'] or "").lower()
                    or search_term in (row['vendor_name'] or "").lower()
                    or search_term in (row['contract_type'] or "").lower()
                    or search_term in (row['description'] or "").lower()
                    or search_term in (row.get('my_role', '') or "").lower()
                    or search_term in (row.get('status', '') or "").lower()
                    or (search_term == 'returned' and row.get('status') == 'returned')
                    or (search_term == 'updated' and row.get('status') in ('updated', 'Updated'))
                    or (search_term == 'review' and row.get('status') == 'Review')
                ]
            
            contracts_table.rows = base_rows
            contracts_table.update()
        
        def clear_filters():
            owner_filter.value = 'All'
            vendor_filter.value = 'All'
            type_filter.value = 'All'
            status_filter.value = 'All'
            search_input.value = ""
            apply_filters()
        
        # Search input for filtering contracts
        with ui.row().classes('w-full ml-4 mr-4 mb-6 gap-2 px-2'):
            search_input = ui.input(placeholder='Search by Contract ID, Vendor, Type, Description, or Manager...').classes(
                'flex-1'
            ).props('outlined dense clearable')
            with search_input.add_slot('prepend'):
                ui.icon('search').classes('text-gray-400')
            ui.button(icon='search', on_click=apply_filters).props('color=primary')
            ui.button(icon='clear', on_click=clear_filters).props('color=secondary')
        
        # Create table after search bar (showing all contracts)
        initial_rows = contract_rows
        contracts_table = ui.table(
            columns=contract_columns,
            column_defaults=contract_columns_defaults,
            rows=initial_rows,
            pagination=10,
            row_key="contract_id"
        ).classes("w-full").props("flat bordered").classes(
            "contracts-table shadow-lg rounded-lg overflow-hidden"
        )
        
        search_input.on_value_change(apply_filters)
        
        # Generate button (moved from header to after table)
        ui.button("Generate", icon="description", on_click=lambda: open_generate_dialog()).props('color=primary').classes('ml-4 mt-4')
        
        # Function to load data asynchronously and update UI
        def load_data_and_update():
            """Load data from database and update the table"""
            nonlocal contract_rows, loading_label
            
            try:
                print("Loading contract updates from database...")
                new_rows = load_data_sync()
                print(f"Received {len(new_rows) if new_rows else 0} rows from database")
                
                if new_rows and len(new_rows) > 0:
                    contract_rows = new_rows
                    # Update filter options with new data
                    vendor_options = ['All'] + sorted(list(set([row['vendor_name'] for row in contract_rows if row.get('vendor_name')])))
                    type_options = ['All'] + sorted(list(set([row['contract_type'] for row in contract_rows if row.get('contract_type')])))
                    vendor_filter.options = vendor_options
                    type_filter.options = type_options
                    print(f"Loaded {len(contract_rows)} contract updates from database")
                else:
                    # Fallback to mock data if database returns empty
                    print("Database returned no data, using mock data as fallback")
                    contract_rows = get_mock_contract_updates()
                    # Update filter options with mock data
                    vendor_options = ['All'] + sorted(list(set([row['vendor_name'] for row in contract_rows if row.get('vendor_name')])))
                    type_options = ['All'] + sorted(list(set([row['contract_type'] for row in contract_rows if row.get('contract_type')])))
                    vendor_filter.options = vendor_options
                    type_filter.options = type_options
                
                # Update table with new data
                if contracts_table:
                    apply_filters()
                    # Update contract_data_map for action handlers
                    contract_data_map.clear()
                    contract_data_map.update({row['contract_id']: row for row in contract_rows})
                
                # Hide loading indicator
                if loading_label:
                    loading_label.visible = False
                    
            except Exception as e:
                print(f"Error loading contract updates: {e}")
                import traceback
                traceback.print_exc()
                # Fallback to mock data
                contract_rows = get_mock_contract_updates()
                # Update filter options with mock data
                vendor_options = ['All'] + sorted(list(set([row['vendor_name'] for row in contract_rows if row.get('vendor_name')])))
                type_options = ['All'] + sorted(list(set([row['contract_type'] for row in contract_rows if row.get('contract_type')])))
                vendor_filter.options = vendor_options
                type_filter.options = type_options
                if contracts_table:
                    apply_filters()
                    # Update contract_data_map for action handlers
                    contract_data_map.clear()
                    contract_data_map.update({row['contract_id']: row for row in contract_rows})
                if loading_label:
                    loading_label.visible = False
        
        # Load data asynchronously after a short delay to allow page to render
        # The timer will call the function once after 200ms to avoid blocking page render
        ui.timer(0.2, load_data_and_update, once=True)
        
        # Tab switching functionality
        current_tab = {'value': 'all'}  # Track current tab
        
        def switch_tab(tab_type):
            """Switch between All Updates and Returned Contracts tabs"""
            current_tab['value'] = tab_type
            
            # Update tab button styles
            if tab_type == 'all':
                all_tab_button.props('color=primary')
                returned_tab_button.props('flat')
                description_label.text = "Review responses provided by Contract Managers or Backups"
            else:
                all_tab_button.props('flat')
                returned_tab_button.props('color=negative')
                description_label.text = "Contracts returned to Contract Managers after review by Contract Admin"
            
            # Filter and update table
            if tab_type == 'returned':
                # Show only returned contracts
                returned_rows = [row for row in contract_rows if row.get('status') == 'returned']
                contracts_table.rows = returned_rows
                # Update count
                if hasattr(contracts_table, 'count_label'):
                    contracts_table.count_label.text = f"Returned Contracts: {len(returned_rows)}"
            else:
                # Show all contracts
                contracts_table.rows = contract_rows
                if hasattr(contracts_table, 'count_label'):
                    contracts_table.count_label.text = f"Total: {len(contract_rows)}"
            
            contracts_table.update()
        
        # Initialize tab
        switch_tab('all')
        
        # Add custom CSS for visual highlighting and toggle styling
        ui.add_css("""
            .contracts-table thead tr {
                background-color: #144c8e !important;
            }
            .contracts-table tbody tr {
                background-color: white !important;
            }
            
            /* Highlight returned contracts with light red background */
            .contracts-table tbody tr:has(.q-btn[label="Returned"]) {
                background-color: #fee2e2 !important;
                border-left: 4px solid #dc2626 !important;
            }
            
            /* Tab button styling */
            .tab-button {
                border-radius: 4px 4px 0 0 !important;
                margin-bottom: -2px !important;
            }
        """)
        
        # Add slot for contract ID with clickable link
        contracts_table.add_slot('body-cell-contract_id', '''
            <q-td :props="props">
                <a v-if="props.row.id" :href="'/contract-info/' + props.row.id" class="text-blue-600 hover:text-blue-800 underline cursor-pointer font-semibold">
                    {{ props.value }}
                </a>
                <span v-else class="text-gray-600 font-semibold">{{ props.value }}</span>
            </q-td>
        ''')
        
        # Add slot for vendor name with clickable link
        contracts_table.add_slot('body-cell-vendor_name', '''
            <q-td :props="props">
                <a v-if="props.row.vendor_id" :href="'/vendor-info/' + props.row.vendor_id" class="text-blue-600 hover:text-blue-800 underline cursor-pointer">
                    {{ props.value }}
                </a>
                <span v-else class="text-gray-600">{{ props.value }}</span>
            </q-td>
        ''')
        
        # Add slot for My Role column with badge styling
        contracts_table.add_slot('body-cell-my_role', '''
            <q-td :props="props">
                <q-badge
                    v-if="props.value === 'Contract Manager'"
                    color="blue"
                    :label="props.value"
                    class="font-semibold"
                />
                <q-badge
                    v-else-if="props.value === 'Backup'"
                    color="orange"
                    text-color="white"
                    :label="props.value"
                    class="font-semibold"
                />
                <q-badge
                    v-else-if="props.value === 'Owner'"
                    color="primary"
                    :label="props.value"
                    class="font-semibold"
                />
                <span v-else class="text-gray-500">{{ props.value || 'N/A' }}</span>
            </q-td>
        ''')
        
        # --- Contract Decision Dialog (open when user clicks status) ---
        selected_contract = {}
        
        with ui.dialog().props("max-width=640px") as contract_decision_dialog, ui.card().classes("w-full max-w-3xl max-h-[90vh] overflow-y-auto p-6"):
            ui.label("Contract Decision").classes("text-h5 mb-4 text-blue-600 font-bold")
            dialog_content = ui.column().classes("w-full gap-4")
        
        def populate_dialog_content():
            """Populate dialog with contract/update data: Decision, Admin comments, Action taken by, Documents & comments, Complete/Cancel."""
            dialog_content.clear()
            update = None
            contract_obj = None
            acted_by_name = "N/A"
            manager_comments = ""
            contract_db_id = selected_contract.get("contract_db_id") or selected_contract.get("id")
            update_id = selected_contract.get("update_id")
            try:
                db2 = SessionLocal()
                try:
                    contract_obj = (
                        db2.query(Contract)
                        .options(
                            joinedload(Contract.documents),
                            joinedload(Contract.termination_documents),
                        )
                        .filter(Contract.id == contract_db_id)
                        .first()
                    )
                    if update_id:
                        update = db2.query(ContractUpdate).filter(ContractUpdate.id == update_id).first()
                    if not update and contract_db_id:
                        update = (
                            db2.query(ContractUpdate)
                            .filter(ContractUpdate.contract_id == contract_db_id)
                            .order_by(ContractUpdate.created_at.desc())
                            .first()
                        )
                    if update and update.response_provided_by_user_id:
                        acted_user = db2.query(User).filter(User.id == update.response_provided_by_user_id).first()
                        if acted_user:
                            acted_by_name = f"{acted_user.first_name} {acted_user.last_name}"
                    if update and update.decision_comments:
                        manager_comments = update.decision_comments
                finally:
                    db2.close()
            except Exception as e:
                print(f"Error loading contract/update for dialog: {e}")
            
            # Build options for decision: match stored value (Renew/Terminate or Extend)
            prev_decision = (update.decision if update and update.decision else None) or selected_contract.get("decision")
            if prev_decision == "Extend":
                prev_decision = "Renew"
            decision_options = ["Terminate", "Renew"]
            initial_decision = prev_decision if prev_decision in decision_options else "Terminate"
            # Parse planned doc name/date from decision_comments if saved earlier; else use existing termination doc
            planned_doc_name, planned_doc_date = "", ""
            if update and update.decision_comments:
                m = re.search(r'\[Planned termination doc: ([^]]*), date: ([^]]*)\]', update.decision_comments)
                if m:
                    planned_doc_name = m.group(1).strip() if m.group(1) != "(not set)" else ""
                    planned_doc_date = m.group(2).strip() if m.group(2) != "(not set)" else ""
            # When reopening after Complete (Review status), show existing termination doc name/date if we have no planned
            if (not planned_doc_name or not planned_doc_date) and contract_obj and contract_obj.termination_documents:
                first_tdoc = contract_obj.termination_documents[0]
                if not planned_doc_name:
                    planned_doc_name = first_tdoc.document_name or ""
                if not planned_doc_date and getattr(first_tdoc, "document_date", None):
                    planned_doc_date = first_tdoc.document_date.strftime("%Y-%m-%d") if hasattr(first_tdoc.document_date, "strftime") else str(first_tdoc.document_date)
            
            with dialog_content:
                # Status badge (same as pending_contracts / contracts requiring attention)
                status_badge = (selected_contract.get("status") or "N/A").replace("updated", "Updated")
                badge_color = "negative" if status_badge == "returned" else ("primary" if status_badge == "Review" else ("positive" if status_badge == "Updated" else "grey"))
                with ui.row().classes("mb-2 items-center gap-2"):
                    ui.label("Status:").classes("text-sm font-medium text-gray-600")
                    ui.badge(status_badge, color=badge_color).classes("text-sm font-semibold")

                # Contract summary + who last took action
                with ui.row().classes("mb-4 p-4 bg-gray-50 rounded-lg w-full"):
                    with ui.column().classes("gap-1"):
                        ui.label(f"Contract ID: {selected_contract.get('contract_id', 'N/A')}").classes("font-bold text-lg")
                        ui.label(f"Vendor: {selected_contract.get('vendor_name', 'N/A')}").classes("text-gray-600")
                        ui.label(f"Expiration Date: {selected_contract.get('expiration_date', 'N/A')}").classes("text-gray-600")
                        ui.label(f"Action taken by: {acted_by_name}").classes("text-gray-600 text-sm")
                
                # Decision section (same as pending_contracts)
                ui.label("Decision").classes("text-lg font-bold")
                decision_select = ui.select(
                    options=decision_options,
                    value=initial_decision
                ).classes("w-full").props("outlined dense")

                end_date_container = ui.column().classes("w-full")
                initial_exp = (update.initial_expiration_date.strftime("%Y-%m-%d") if update and getattr(update, 'initial_expiration_date', None) and hasattr(update.initial_expiration_date, 'strftime') else None) or selected_contract.get("initial_expiration", "") or selected_contract.get("expiration_date", "")
                with end_date_container:
                    end_date_input = ui.input("End Date (required for Renew)", value=initial_exp).props("type=date outlined dense").classes("w-full")
                    def _base_date():
                        raw = (end_date_input.value or "").strip() or initial_exp or ""
                        if not raw:
                            return date.today()
                        try:
                            return datetime.strptime(raw.replace("/", "-")[:10], "%Y-%m-%d").date()
                        except Exception:
                            return date.today()
                    def _set_end_date_years(years: int):
                        d = _base_date()
                        try:
                            new_d = d.replace(year=d.year + years)
                        except ValueError:
                            new_d = d.replace(day=28, year=d.year + years)
                        end_date_input.value = new_d.strftime("%Y-%m-%d")
                    with ui.row().classes("gap-2 items-center mt-1"):
                        ui.button("+1 year", on_click=lambda: _set_end_date_years(1)).props("flat dense color=primary")
                        ui.button("+2 years", on_click=lambda: _set_end_date_years(2)).props("flat dense color=primary")

                term_doc_container = ui.column().classes("w-full")
                with term_doc_container:
                    ui.label("Termination Document (required for Terminate). Upload below if missing.").classes("text-sm font-medium")
                    term_doc_upload_ref = {"name": None, "content": None}
                    term_doc_name_input = ui.input("Document name", placeholder="e.g. Termination letter", value=planned_doc_name).props("outlined dense").classes("w-full")
                    term_doc_date_input = ui.input("Issue Date", value=planned_doc_date).props("type=date outlined dense").classes("w-full")

                    async def on_term_file_upload(e):
                        term_doc_upload_ref["name"] = e.file.name
                        term_doc_upload_ref["content"] = await e.file.read()

                    ui.upload(on_upload=on_term_file_upload, auto_upload=True, label="Upload PDF (required for Terminate)").props("accept=.pdf outlined dense").classes("w-full")

                def toggle_decision_requirements():
                    if decision_select.value == "Renew":
                        end_date_container.visible = True
                        term_doc_container.visible = False
                    else:
                        end_date_container.visible = False
                        term_doc_container.visible = True
                
                decision_select.on_value_change(lambda e: toggle_decision_requirements())
                toggle_decision_requirements()
                
                # Contract Admin comments: view-only for manager; editable for admin when status is Review (for Send back reason)
                ui.label("Contract Admin Comments (Review)").classes("text-lg font-bold mt-2")
                admin_comments_text = (update.admin_comments if update and update.admin_comments else "") or selected_contract.get("admin_comments", "") or "No comments from Contract Admin."
                status_raw = selected_contract.get("status_raw", "")
                is_admin_review = status_raw == ContractUpdateStatus.PENDING_REVIEW.value and current_user_role == UserRole.CONTRACT_ADMIN.value
                admin_remarks_input = ui.textarea(value=admin_comments_text).classes("w-full").props(
                    "outlined" + (" readonly" if not is_admin_review else "")
                )
                
                # Documents & Comments (same as pending_contracts)
                ui.label("Documents & Comments").classes("text-lg font-bold mt-2")
                with ui.card().classes("p-4 bg-white border w-full"):
                    ui.label("Comments (Contract Manager / Backup / Owner can add comments below):").classes("font-medium")
                    manager_comments_input = ui.textarea(value=manager_comments or "").classes("w-full").props("outlined")
                    ui.separator()
                    ui.label("Contract documents:").classes("font-medium mt-2")
                    if contract_obj and contract_obj.documents:
                        for doc in contract_obj.documents:
                            with ui.row().classes("items-center justify-between w-full gap-2 py-1"):
                                ui.label(doc.custom_document_name or doc.file_name).classes("text-sm")
                                doc_date_str = doc.document_signed_date.strftime("%Y-%m-%d") if getattr(doc.document_signed_date, "strftime", None) else str(doc.document_signed_date)
                                ui.label(f"Issue date: {doc_date_str}").classes("text-xs text-gray-500")
                                ui.button("Download", icon="download", on_click=lambda p=doc.file_path, n=doc.file_name: ui.download(p, filename=n)).props("flat color=primary size=sm")
                    else:
                        ui.label("No contract documents uploaded.").classes("text-gray-500 italic")
                    ui.label("Termination documents:").classes("font-medium mt-2")
                    if contract_obj and contract_obj.termination_documents:
                        for tdoc in contract_obj.termination_documents:
                            with ui.row().classes("items-center justify-between w-full gap-2 py-1"):
                                ui.label(tdoc.document_name).classes("text-sm")
                                tdate_str = tdoc.document_date.strftime("%Y-%m-%d") if getattr(tdoc.document_date, "strftime", None) else str(tdoc.document_date)
                                ui.label(f"Document date: {tdate_str}").classes("text-xs text-gray-500")
                                ui.button("Download", icon="download", on_click=lambda p=tdoc.file_path, n=tdoc.file_name: ui.download(p, filename=n)).props("flat color=primary size=sm")
                    else:
                        ui.label("No termination documents yet. Upload above when Decision is Terminate.").classes("text-gray-500 italic")
                
                # Complete, Save, Cancel (same as pending_contracts). For admin/review: Save is replaced by Send Back.
                with ui.row().classes("gap-3 justify-end mt-4 w-full"):
                    complete_btn = ui.button("Complete", icon="check_circle").props("color=positive")
                    if status_raw == ContractUpdateStatus.PENDING_REVIEW.value and current_user_role == UserRole.CONTRACT_ADMIN.value:
                        save_btn = ui.button("Send Back", icon="undo").props("color=negative")
                    else:
                        save_btn = ui.button("Save", icon="save").props("color=primary")
                    ui.button("Cancel", icon="cancel", on_click=contract_decision_dialog.close).props("flat color=grey")
                with ui.row().classes("gap-2 items-center mt-2") as loading_row:
                    ui.spinner(size="sm", color="primary")
                    ui.label("Completing…")
                loading_row.set_visibility(False)

                def do_save():
                    """Save changes without changing status (manager, returned only)."""
                    if status_raw != ContractUpdateStatus.RETURNED.value or current_user_role == UserRole.CONTRACT_ADMIN.value:
                        return
                    nonlocal contract_rows
                    try:
                        db3 = SessionLocal()
                        try:
                            upd = db3.query(ContractUpdate).filter(ContractUpdate.id == (update_id or 0)).first()
                            if not upd and contract_db_id:
                                upd = (
                                    db3.query(ContractUpdate)
                                    .filter(ContractUpdate.contract_id == contract_db_id)
                                    .order_by(ContractUpdate.created_at.desc())
                                    .first()
                                )
                            if not upd:
                                ui.notify("Contract update not found", type="negative")
                                return
                            comments = manager_comments_input.value or ""
                            if decision_select.value == "Terminate":
                                tname = (term_doc_name_input.value or "").strip()
                                tdate = (term_doc_date_input.value or "").strip()
                                if tname or tdate:
                                    comments = (comments + "\n" if comments else "") + f"[Planned termination doc: {tname or '(not set)'}, date: {tdate or '(not set)'}]"
                            upd.decision_comments = comments
                            dec = decision_select.value
                            if dec:
                                upd.decision = "Extend" if dec == "Renew" else dec
                            end_val = (end_date_input.value or "").strip() if dec == "Renew" else None
                            if end_val:
                                try:
                                    upd.initial_expiration_date = datetime.strptime(end_val.replace("/", "-"), "%Y-%m-%d").date()
                                except Exception:
                                    pass
                            upd.updated_at = datetime.utcnow()
                            db3.commit()
                            ui.notify("Changes saved. Status remains Returned.", type="positive")
                            reload_contract_updates()
                            apply_filters()
                        finally:
                            db3.close()
                    except Exception as e:
                        ui.notify(f"Error saving: {e}", type="negative")
                    contract_decision_dialog.close()

                def do_send_back():
                    """Send back: admin changes status from Review to Returned."""
                    if status_raw != ContractUpdateStatus.PENDING_REVIEW.value or current_user_role != UserRole.CONTRACT_ADMIN.value:
                        return
                    reason = (admin_remarks_input.value or "").strip()
                    if not reason:
                        ui.notify("Please provide a reason for sending back.", type="negative")
                        return
                    nonlocal contract_rows
                    try:
                        db3 = SessionLocal()
                        try:
                            upd = db3.query(ContractUpdate).filter(ContractUpdate.id == (update_id or 0)).first()
                            if not upd and contract_db_id:
                                upd = (
                                    db3.query(ContractUpdate)
                                    .filter(ContractUpdate.contract_id == contract_db_id)
                                    .order_by(ContractUpdate.created_at.desc())
                                    .first()
                                )
                            if not upd:
                                ui.notify("Contract update not found", type="negative")
                                return
                            upd.status = ContractUpdateStatus.RETURNED
                            upd.admin_comments = reason
                            upd.returned_reason = reason
                            upd.returned_date = datetime.utcnow()
                            upd.updated_at = datetime.utcnow()
                            db3.commit()
                            ui.notify("Sent back to Contract Manager. Status is now Returned.", type="info")
                            reload_contract_updates()
                            apply_filters()
                            if current_tab["value"] == "returned":
                                switch_tab("returned")
                        finally:
                            db3.close()
                    except Exception as e:
                        ui.notify(f"Error sending back: {e}", type="negative")
                    contract_decision_dialog.close()

                def do_complete():
                    status_raw = (selected_contract.get("status_raw", "") or selected_contract.get("status", "") or "").strip().lower()
                    log.info("Contract Updates Complete clicked: status_raw=%r current_user_role=%s update_id=%s contract_db_id=%s",
                             status_raw, current_user_role, selected_contract.get("update_id"), selected_contract.get("contract_db_id") or selected_contract.get("id"))
                    # AC 1: Complete – Returned: Manager/Backup/Owner or Admin resubmits → update status to Review
                    if status_raw == ContractUpdateStatus.RETURNED.value:
                        log.info("Entering RETURNED branch: running complete in background")
                        dec = decision_select.value
                        end_val = (end_date_input.value or "").strip() if dec == "Renew" else None
                        if dec == "Renew" and not end_val:
                            ui.notify("End date is required for Renew.", type="negative")
                            return
                        if dec == "Terminate":
                            has_existing = contract_obj and contract_obj.termination_documents and len(contract_obj.termination_documents) > 0
                            has_upload = term_doc_upload_ref.get("content")
                            if not has_existing and not has_upload:
                                ui.notify("Please upload the Termination Document", type="negative")
                                return
                            if has_upload:
                                tname = (term_doc_name_input.value or "").strip()
                                tdate = (term_doc_date_input.value or "").strip()
                                if not tname or not tdate:
                                    ui.notify("Document name and Issue Date are required for the uploaded termination document.", type="negative")
                                    return
                        loading_row.set_visibility(True)
                        complete_btn.disable()
                        save_btn.disable()

                        async def run_returned_complete():
                            tname = (term_doc_name_input.value or "").strip()
                            tdate = (term_doc_date_input.value or "").strip()
                            term_content = term_doc_upload_ref.get("content")
                            term_fname = term_doc_upload_ref.get("name") or "document.pdf"
                            mgr_comments = (manager_comments_input.value or "").strip()
                            has_doc_final = (bool(contract_obj and contract_obj.documents) if dec == "Renew"
                                else bool(term_content or (contract_obj and contract_obj.termination_documents)))
                            result = (False, "Request failed")
                            try:
                                result = await run.io_bound(
                                    _complete_returned_update_blocking,
                                    update_id,
                                    contract_db_id,
                                    current_user_id,
                                    dec,
                                    end_val,
                                    tname,
                                    tdate,
                                    term_content,
                                    term_fname,
                                    mgr_comments,
                                    has_doc_final,
                                )
                            except Exception as e:
                                result = (False, str(e))
                                log.exception("Returned complete failed")
                            try:
                                with contract_decision_dialog:
                                    loading_row.set_visibility(False)
                                    complete_btn.enable()
                                    save_btn.enable()
                                    if result[0]:
                                        ui.notify("Contract resubmitted for review. It has been routed to Contract Admin.", type="positive")
                                        try:
                                            reload_contract_updates()
                                            apply_filters()
                                        except Exception as e:
                                            log.warning("reload/apply_filters after returned complete: %s", e)
                                        try:
                                            switch_tab("all")
                                        except Exception:
                                            pass
                                        contract_decision_dialog.close()
                                    else:
                                        ui.notify(result[1] or "Request failed", type="negative")
                            except Exception as e:
                                log.warning("UI update after returned complete: %s", e)
                                try:
                                    loading_row.set_visibility(False)
                                    complete_btn.enable()
                                    save_btn.enable()
                                    ui.notify(f"Error: {e}", type="negative")
                                except Exception:
                                    pass

                        if not hasattr(contract_decision_dialog, "_complete_tasks"):
                            contract_decision_dialog._complete_tasks = set()
                        task = asyncio.create_task(run_returned_complete())
                        contract_decision_dialog._complete_tasks.add(task)
                        task.add_done_callback(lambda t: contract_decision_dialog._complete_tasks.discard(t))
                        return
                    # AC 2 & 3: Complete – Review (Contract Admin only): Renew or Terminate
                    # Only Contract Admin can complete when status is Review (pending_review)
                    if status_raw == ContractUpdateStatus.PENDING_REVIEW.value and current_user_role != UserRole.CONTRACT_ADMIN.value:
                        ui.notify("This contract is awaiting Contract Admin review. Only Contract Admin can complete the Renew or Terminate decision.", type="info")
                        return
                    if status_raw != ContractUpdateStatus.PENDING_REVIEW.value:
                        ui.notify("Only contracts in Review status can be completed with Renew or Terminate.", type="info")
                        return
                    decision_value = decision_select.value
                    if decision_value == "Renew":
                        end_val = (end_date_input.value or "").strip()
                        if not end_val:
                            ui.notify("End date is required when decision is Renew.", type="negative")
                            return
                    if decision_value == "Terminate":
                        has_existing = contract_obj and contract_obj.termination_documents and len(contract_obj.termination_documents) > 0
                        has_upload = term_doc_upload_ref.get("content")
                        if not has_existing and not has_upload:
                            ui.notify("Please upload the Termination Document", type="negative")
                            return
                        if has_upload:
                            tname = (term_doc_name_input.value or "").strip()
                            tdate = (term_doc_date_input.value or "").strip()
                            if not tname or not tdate:
                                ui.notify("Document name and Issue Date are required for the uploaded termination document.", type="negative")
                                return
                    nonlocal contract_rows
                    try:
                        # Terminate with upload: store termination document first
                        if decision_value == "Terminate" and term_doc_upload_ref.get("content"):
                            tname = (term_doc_name_input.value or "").strip()
                            tdate = (term_doc_date_input.value or "").strip()
                            try:
                                with httpx.Client(timeout=30.0) as client:
                                    r = client.post(
                                        f"http://localhost:8000/api/v1/contracts/{contract_db_id}/termination-documents",
                                        data={"document_name": tname, "document_date": tdate},
                                        files={"file": (term_doc_upload_ref["name"] or "document.pdf", term_doc_upload_ref["content"], "application/pdf")},
                                    )
                                if r.status_code not in (200, 201):
                                    ui.notify(r.json().get("detail", "Failed to store termination document"), type="negative")
                                    return
                            except Exception as e:
                                ui.notify(f"Error storing termination document: {e}", type="negative")
                                return
                        db3 = SessionLocal()
                        try:
                            upd = db3.query(ContractUpdate).filter(ContractUpdate.id == (update_id or 0)).first()
                            if not upd and contract_db_id:
                                upd = (
                                    db3.query(ContractUpdate)
                                    .filter(ContractUpdate.contract_id == contract_db_id)
                                    .order_by(ContractUpdate.created_at.desc())
                                    .first()
                                )
                            if not upd:
                                upd = ContractUpdate(contract_id=contract_db_id, status=ContractUpdateStatus.COMPLETED)
                                db3.add(upd)
                            contract_db = db3.query(Contract).filter(Contract.id == contract_db_id).first()
                            if not contract_db:
                                ui.notify("Contract not found", type="negative")
                                return
                            if decision_value == "Renew":
                                from datetime import datetime as dt
                                try:
                                    new_end = dt.strptime((end_date_input.value or "").strip(), "%Y-%m-%d").date()
                                except Exception:
                                    ui.notify("Invalid end date.", type="negative")
                                    return
                                contract_db.end_date = new_end
                                contract_db.last_modified_by = app.storage.user.get("username", "SYSTEM") if app.storage.user else "SYSTEM"
                                contract_db.last_modified_date = datetime.utcnow()
                                upd.initial_expiration_date = new_end
                            elif decision_value == "Terminate":
                                # AC 3: Update contract status to Inactive (Terminated)
                                contract_db.status = ContractStatusType.TERMINATED
                                contract_db.contract_termination = ContractTerminationType.YES
                                contract_db.last_modified_by = app.storage.user.get("username", "SYSTEM") if app.storage.user else "SYSTEM"
                                contract_db.last_modified_date = datetime.utcnow()
                            upd.status = ContractUpdateStatus.COMPLETED
                            upd.decision = "Renew" if decision_value == "Renew" else "Terminate"
                            upd.decision_comments = manager_comments_input.value or ""
                            upd.updated_at = datetime.utcnow()
                            db3.commit()
                            ui.notify("Review completed", type="positive")
                            reload_contract_updates()
                            apply_filters()
                            if current_tab['value'] == 'returned':
                                switch_tab('returned')
                        finally:
                            db3.close()
                    except Exception as e:
                        ui.notify(f"Error completing review: {e}", type="negative")
                        import traceback
                        traceback.print_exc()
                    contract_decision_dialog.close()

                # Bind handlers so clicks reach the server (must run when dialog content is built, not inside do_complete)
                complete_btn.on_click(do_complete)
                if status_raw == ContractUpdateStatus.PENDING_REVIEW.value and current_user_role == UserRole.CONTRACT_ADMIN.value:
                    save_btn.on_click(do_send_back)
                else:
                    save_btn.on_click(do_save)
        
        def open_contract_decision_dialog(row: dict) -> None:
            """Open the Contract Decision dialog for the clicked contract row."""
            # If table slot passed only column fields, resolve full row from contract_rows so we have update_id and id
            contract_id_key = row.get("contract_id")
            if (row.get("update_id") is None or row.get("id") is None) and contract_id_key and contract_rows:
                for full_row in contract_rows:
                    if full_row.get("contract_id") == contract_id_key and full_row.get("status") == row.get("status"):
                        row = full_row
                        break
            selected_contract.clear()
            selected_contract["contract_id"] = row.get("contract_id", "")
            selected_contract["contract_db_id"] = row.get("id", 0)
            selected_contract["update_id"] = row.get("update_id")
            selected_contract["vendor_name"] = row.get("vendor_name", "N/A")
            selected_contract["expiration_date"] = row.get("expiration_date", "N/A")
            selected_contract["admin_comments"] = row.get("admin_comments", "")
            selected_contract["decision"] = row.get("decision")
            selected_contract["initial_expiration"] = row.get("initial_expiration", "")
            selected_contract["status"] = row.get("status", "")
            selected_contract["status_raw"] = row.get("status_raw", row.get("status", ""))
            populate_dialog_content()
            contract_decision_dialog.open()
        
        def on_status_click(e) -> None:
            try:
                row = e.args[0] if isinstance(e.args, (list, tuple)) and len(e.args) > 0 else e.args
                if not isinstance(row, dict):
                    ui.notify("Could not open Contract Decision dialog: invalid row data", type="negative")
                    return
                row_id = row.get("id")
                contract_id = row.get("contract_id")
                if (row_id is None or row_id == 0) and not contract_id:
                    ui.notify("Could not open Contract Decision dialog: missing contract data", type="negative")
                    return
                open_contract_decision_dialog(row)
            except Exception as ex:
                ui.notify(f"Could not open Contract Decision dialog: {ex}", type="negative")
        
        contracts_table.on("status_click", on_status_click)
        
        # Add slot for status column: clickable buttons per status, opens Contract Decision pop-up
        contracts_table.add_slot('body-cell-status', '''
            <q-td :props="props">
                <div v-if="props.row.status === 'returned'" class="flex items-center justify-center">
                    <q-btn
                        label="Returned"
                        color="negative"
                        size="sm"
                        icon="undo"
                        dense
                        class="font-semibold cursor-pointer"
                        @click="$parent.$emit('status_click', props.row)"
                    />
                </div>
                <div v-else-if="props.row.status === 'Updated' || props.row.status === 'updated'" class="flex items-center justify-center">
                    <q-btn
                        label="Updated"
                        size="sm"
                        icon="check_circle"
                        dense
                        color="positive"
                        class="font-semibold cursor-pointer"
                        @click="$parent.$emit('status_click', props.row)"
                    />
                </div>
                <div v-else-if="props.row.status === 'Review'" class="flex items-center justify-center">
                    <q-btn
                        label="Review"
                        size="sm"
                        icon="rate_review"
                        dense
                        color="primary"
                        class="font-semibold cursor-pointer"
                        @click="$parent.$emit('status_click', props.row)"
                    />
                </div>
                <div v-else class="flex items-center justify-center">
                    <q-btn
                        flat
                        dense
                        no-caps
                        :label="props.row.status"
                        color="grey"
                        class="font-semibold cursor-pointer"
                        @click="$parent.$emit('status_click', props.row)"
                    />
                </div>
            </q-td>
        ''')
        
        # Function to generate Excel report
        def open_generate_dialog():
            """Open dialog for date range selection and report generation"""
            with ui.dialog() as dialog, ui.card().classes('p-6 w-full max-w-md'):
                ui.label("Generate Contract Updates Report").classes("text-h6 font-bold mb-4")
                
                with ui.column().classes('gap-4 w-full'):
                    ui.label("Select date range for contract updates:").classes("text-sm text-gray-600")
                    
                    start_date_input = ui.input("Start Date", placeholder="YYYY-MM-DD").props('type=date').classes('w-full')
                    end_date_input = ui.input("End Date", placeholder="YYYY-MM-DD").props('type=date').classes('w-full')
                    
                    # Set default dates (last 6 months)
                    today = datetime.now()
                    default_start = (today - timedelta(days=180)).strftime("%Y-%m-%d")
                    default_end = today.strftime("%Y-%m-%d")
                    start_date_input.value = default_start
                    end_date_input.value = default_end
                    
                    ui.label("The report will include all contract updates.").classes("text-xs text-gray-500 italic")
                    
                    with ui.row().classes('gap-2 justify-end w-full mt-4'):
                        ui.button("Cancel", on_click=dialog.close).props('flat')
                        ui.button("Generate & Download", icon="download", 
                                 on_click=lambda: generate_excel_report(start_date_input.value, end_date_input.value, dialog)).props('color=primary')
                
                dialog.open()
        
        def generate_excel_report(start_date_str, end_date_str, dialog):
            """Generate Excel report for contract updates"""
            try:
                if not PANDAS_AVAILABLE:
                    ui.notify("Excel export requires pandas library. Please install it: pip install pandas openpyxl", type="negative")
                    dialog.close()
                    return
                
                if not contract_rows:
                    ui.notify("No contract updates available for export", type="warning")
                    dialog.close()
                    return
                
                # Prepare data for Excel
                report_data = []
                for contract in contract_rows:
                    report_data.append({
                        "Contract ID": contract.get('contract_id', ''),
                        "Contract Type": contract.get('contract_type', ''),
                        "Description": contract.get('description', ''),
                        "Vendor": contract.get('vendor_name', ''),
                        "Expiration Date": contract.get('expiration_date', ''),
                        "Status": contract.get('status', ''),
                        "Manager": contract.get('manager', ''),
                        "Response Date": contract.get('response_date', ''),
                    })
                
                # Create DataFrame
                df = pd.DataFrame(report_data)
                
                # Create Excel file in memory
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Contract Updates')
                    
                    # Get the worksheet
                    worksheet = writer.sheets['Contract Updates']
                    
                    # Auto-adjust column widths
                    for column in worksheet.columns:
                        max_length = 0
                        column_letter = column[0].column_letter
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except (AttributeError, TypeError):
                                pass
                        adjusted_width = min(max_length + 2, 50)
                        worksheet.column_dimensions[column_letter].width = adjusted_width
                
                output.seek(0)
                
                # Convert to base64 for download
                excel_data = output.getvalue()
                b64_data = base64.b64encode(excel_data).decode()
                
                # Generate filename
                filename = f"Contract_Updates_Report_{start_date_str}_to_{end_date_str}.xlsx"
                
                # Trigger download using JavaScript
                ui.run_javascript(f'''
                    const link = document.createElement('a');
                    link.href = 'data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64_data}';
                    link.download = '{filename}';
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                ''')
                
                ui.notify(f"Report generated successfully! {len(contract_rows)} contract(s) exported.", type="positive")
                dialog.close()
                
            except Exception as e:
                ui.notify(f"Error generating report: {str(e)}", type="negative")
                import traceback
                traceback.print_exc()
        
        # Handler functions for actions
        def view_response(row):
            """Open dialog to view response and document"""
            with ui.dialog() as dialog, ui.card().classes('p-6 w-full max-w-3xl'):
                ui.label(f"Response for Contract: {row['contract_id']}").classes("text-h6 font-bold mb-4")
                
                with ui.column().classes('gap-4 w-full'):
                    ui.label(f"Contract Owner: {row['manager']}").classes("text-base")
                    ui.label(f"Response Provided By: {row['response_provided_by']}").classes("text-base")
                    ui.label(f"Response Date: {row['response_date']}").classes("text-base")
                    
                    ui.separator()
                    
                    ui.label("Response Details:").classes("text-base font-semibold")
                    ui.label("The contract manager has reviewed and provided feedback on this contract. "
                            "All required information has been updated as per the notification window requirements.").classes("text-sm text-gray-700")
                    
                    if row.get('has_document', False):
                        ui.label("Document Available: Yes").classes("text-base font-semibold text-green-600")
                        with ui.row().classes('gap-2'):
                            ui.button("View Document", icon="description", on_click=lambda: ui.notify("Document viewer would open here", type="info")).props('color=primary')
                            ui.button("Download Document", icon="download", on_click=lambda: ui.notify("Document download would start here", type="info")).props('color=secondary')
                    else:
                        ui.label("Document Available: No").classes("text-base font-semibold text-orange-600")
                    
                    ui.separator()
                    
                    with ui.row().classes('gap-2 justify-end'):
                        ui.button("Close", on_click=dialog.close).props('flat')
                        ui.button("Edit Information", icon="edit", on_click=lambda: edit_contract_info(row, dialog)).props('color=primary')
            
            dialog.open()
        
        def edit_contract_info(row, parent_dialog=None):
            """Open dialog to edit contract information, retaining previous information if unchanged"""
            if parent_dialog:
                parent_dialog.close()
            
            with ui.dialog() as edit_dialog, ui.card().classes('p-6 w-full max-w-2xl'):
                ui.label(f"Edit Contract Information: {row['contract_id']}").classes("text-h6 font-bold mb-4")
                
                # Show note about retaining previous information if this is a returned contract
                is_returned = row.get('status') == 'returned'
                if is_returned:
                    with ui.card().classes('p-3 bg-red-50 border border-red-200 mb-4'):
                        ui.label("⚠️ This contract has been returned for revision. All fields are pre-populated with your initial submission.").classes("text-sm text-red-700 font-semibold")
                
                with ui.column().classes('gap-4 w-full'):
                    # Pre-populate with initial values for returned contracts, otherwise use current values
                    initial_vendor = row.get('initial_vendor', row.get('vendor_name', ''))
                    initial_type = row.get('initial_type', row.get('contract_type', ''))
                    initial_desc = row.get('initial_description', row.get('description', ''))
                    initial_exp = row.get('initial_expiration', row.get('expiration_date', ''))
                    
                    contract_id_input = ui.input("Contract ID", value=row['contract_id']).classes('w-full').props('readonly')
                    vendor_input = ui.input("Vendor Name", value=initial_vendor if is_returned else row.get('vendor_name', '')).classes('w-full')
                    type_input = ui.input("Contract Type", value=initial_type if is_returned else row.get('contract_type', '')).classes('w-full')
                    description_input = ui.textarea("Description", value=initial_desc if is_returned else row.get('description', '')).classes('w-full')
                    expiration_input = ui.input("Expiration Date", value=initial_exp if is_returned else row.get('expiration_date', '')).props('type=date').classes('w-full')
                    manager_input = ui.input("Contract Owner", value=row['manager']).classes('w-full').props('readonly')
                    
                    # Show Contract Admin comments for returned contracts (view-only)
                    if is_returned:
                        ui.separator()
                        with ui.card().classes('p-4 bg-yellow-50 border-2 border-yellow-300'):
                            with ui.row().classes('items-center gap-2 mb-2'):
                                ui.icon('comment', color='yellow-800', size='sm')
                                ui.label("Contract Admin Comments (View Only):").classes("text-sm font-semibold text-yellow-800")
                            admin_comments_text = row.get('admin_comments', 'No comments provided by Contract Admin.')
                            ui.textarea("", value=admin_comments_text).classes('w-full').props('readonly outlined').style('background-color: white; min-height: 80px;')
                    
                    # Show returned reason if available
                    if is_returned and row.get('returned_reason'):
                        with ui.card().classes('p-3 bg-orange-50 border border-orange-200 mt-2'):
                            ui.label("Reason for Return:").classes("text-sm font-semibold text-orange-700 mb-1")
                            ui.label(row.get('returned_reason', '')).classes("text-sm text-orange-900")
                    
                    # Show previous values if this is a returned contract with previous response
                    if is_returned and row.get('previous_response'):
                        ui.separator()
                        ui.label("Previous Response (for reference):").classes("text-sm font-semibold text-gray-600")
                        prev_info = row.get('previous_response', {})
                        ui.label(f"Previous Description: {prev_info.get('response', 'N/A')}").classes("text-xs text-gray-500")
                    
                    with ui.row().classes('gap-2 justify-end w-full mt-4'):
                        ui.button("Cancel", on_click=edit_dialog.close).props('flat')
                        ui.button("Save Changes", icon="save", on_click=lambda: save_contract_changes(row, {
                            'contract_id': contract_id_input.value,
                            'vendor_name': vendor_input.value,
                            'contract_type': type_input.value,
                            'description': description_input.value,
                            'expiration_date': expiration_input.value,
                            'manager': manager_input.value
                        }, edit_dialog)).props('color=primary')
                
                edit_dialog.open()
        
        def save_contract_changes(original_row, new_data, dialog):
            """Save changes to contract"""
            try:
                update_id = original_row.get('update_id') or original_row.get('id')
                if not update_id:
                    ui.notify("Error: Contract update ID not found", type="negative")
                    return
                
                # Prepare update data
                update_payload = {
                    "initial_vendor_name": new_data.get('vendor_name', original_row.get('vendor_name')),
                    "initial_contract_type": new_data.get('contract_type', original_row.get('contract_type')),
                    "initial_description": new_data.get('description', original_row.get('description')),
                    "initial_expiration_date": new_data.get('expiration_date', original_row.get('expiration_date')),
                }
                
                # If this is a returned contract being corrected, mark as updated
                if original_row.get('status') == 'returned':
                    update_payload["status"] = "updated"
                
                with httpx.Client(timeout=30.0) as client:
                    response = client.patch(
                        f"http://localhost:8000/api/v1/contract-updates/{update_id}",
                        json=update_payload
                    )
                    
                    if response.status_code == 200:
                        # Also update the contract itself if needed
                        # TODO: Add API call to update contract details if contract_id is available
                        
                        ui.notify(f"Changes saved for contract {original_row['contract_id']}", type="positive")
                        dialog.close()
                        # Reload data
                        reload_contract_updates()
                        apply_filters()
                        # Refresh tab if we're on returned contracts tab
                        if current_tab['value'] == 'returned':
                            switch_tab('returned')
                    else:
                        ui.notify(f"Error saving changes: {response.status_code}", type="negative")
            except Exception as e:
                print(f"Error saving contract changes: {e}")
                ui.notify(f"Error saving changes: {str(e)}", type="negative")
        
        def complete_contract(row):
            """Complete and approve contract update, or process returned contract"""
            is_returned_contract = row.get('status') == 'returned'
            
            with ui.dialog() as dialog, ui.card().classes('p-6'):
                if is_returned_contract:
                    ui.label("Process Returned Contract").classes("text-h6 font-bold mb-4")
                    ui.label(f"Process contract {row['contract_id']} and route it to the next step in the workflow?").classes("mb-4")
                    button_text = "Process & Route"
                    button_icon = "forward"
                else:
                    ui.label("Complete Contract Update").classes("text-h6 font-bold mb-4")
                    ui.label(f"Are you sure you want to complete and approve the update for contract {row['contract_id']}?").classes("mb-4")
                    button_text = "Complete"
                    button_icon = "check_circle"
                
                with ui.row().classes('gap-2 justify-end'):
                    ui.button("Cancel", on_click=dialog.close).props('flat')
                    ui.button(button_text, icon=button_icon, on_click=lambda: confirm_complete(row, dialog)).props('color=positive')
                
                dialog.open()
        
        def confirm_complete(row, dialog):
            """Confirm completion - process task and route to next workflow step"""
            try:
                update_id = row.get('update_id') or row.get('id')
                if not update_id:
                    ui.notify("Error: Contract update ID not found", type="negative")
                    return
                
                is_returned_contract = row.get('status') == 'returned'
                
                # Update status to completed
                with httpx.Client(timeout=30.0) as client:
                    response = client.patch(
                        f"http://localhost:8000/api/v1/contract-updates/{update_id}",
                        json={"status": "completed"}
                    )
                    
                    if response.status_code == 200:
                        # Optionally delete the update entry to remove it from the list
                        client.delete(
                            f"http://localhost:8000/api/v1/contract-updates/{update_id}"
                        )
                        
                        if is_returned_contract:
                            message = f"Contract {row['contract_id']} has been processed and routed to the next workflow step"
                        else:
                            message = f"Contract {row['contract_id']} has been completed and approved"
                        
                        ui.notify(message, type="positive")
                        dialog.close()
                        # Reload data
                        reload_contract_updates()
                        apply_filters()
                        # Refresh tab if we're on returned contracts tab
                        if current_tab['value'] == 'returned':
                            switch_tab('returned')
                    else:
                        ui.notify(f"Error processing contract: {response.status_code}", type="negative")
            except Exception as e:
                print(f"Error completing contract: {e}")
                ui.notify(f"Error processing contract: {str(e)}", type="negative")
        
        def send_back_contract(row):
            """Send contract back for revision"""
            with ui.dialog() as dialog, ui.card().classes('p-6 w-full max-w-md'):
                ui.label("Send Contract Back").classes("text-h6 font-bold mb-4")
                ui.label(f"Send contract {row['contract_id']} back for revision?").classes("mb-2")
                
                reason_input = ui.textarea("Reason (optional)", placeholder="Provide reason for sending back...").classes('w-full mb-4')
                
                with ui.row().classes('gap-2 justify-end'):
                    ui.button("Cancel", on_click=dialog.close).props('flat')
                    ui.button("Send Back", icon="undo", on_click=lambda: confirm_send_back(row, reason_input.value, dialog)).props('color=negative')
                
                dialog.open()
        
        def confirm_send_back(row, reason, dialog):
            """Confirm send back"""
            # TODO: Implement API call to send back contract
            message = f"Contract {row['contract_id']} has been sent back for revision"
            if reason:
                message += f" (Reason: {reason})"
            ui.notify(message, type="info")
            dialog.close()
            # Remove from list (or mark as sent back)
            contract_rows[:] = [r for r in contract_rows if r['contract_id'] != row['contract_id']]
            apply_filters()
        
        # Create a mapping of contract IDs to row data for action handlers
        # Initialize as empty dict, will be populated when data loads
        contract_data_map = {}
        
        def open_actions_for_contract(contract_id):
            """Open actions dialog for a specific contract"""
            row = contract_data_map.get(contract_id)
            if not row:
                ui.notify(f"Contract {contract_id} not found", type="negative")
                return
            
            with ui.dialog() as actions_dialog, ui.card().classes('p-6'):
                ui.label(f"Actions for Contract: {contract_id}").classes("text-h6 font-bold mb-4")
                
                with ui.column().classes('gap-3 w-full'):
                    ui.button("View Response", icon="description", 
                             on_click=lambda: [view_response(row), actions_dialog.close()]).props('color=primary full-width')
                    ui.button("Edit Information", icon="edit", 
                             on_click=lambda: [edit_contract_info(row, actions_dialog), actions_dialog.close()]).props('color=secondary full-width')
                    ui.button("Complete", icon="check_circle", 
                             on_click=lambda: [complete_contract(row), actions_dialog.close()]).props('color=positive full-width')
                    ui.button("Send Back", icon="undo", 
                             on_click=lambda: [send_back_contract(row), actions_dialog.close()]).props('color=negative full-width')
                    ui.button("Cancel", on_click=actions_dialog.close).props('flat full-width')
                
                actions_dialog.open()
        
        # Store the handler function in a way that can be accessed from JavaScript
        # We'll use ui.run_javascript to bridge the gap
        # For now, let's use a simpler approach: make the Response button open the response dialog
        # which already has Edit, Complete, and Send Back buttons
        
        # Update view_response to include action buttons and previous response info
        def view_response_with_actions(row):
            """Open response dialog with action buttons and previous response information"""
            is_returned = row.get('status') == 'returned'
            
            with ui.dialog() as dialog, ui.card().classes('p-6 w-full max-w-3xl'):
                ui.label(f"Response for Contract: {row['contract_id']}").classes("text-h6 font-bold mb-4")
                
                # Show returned badge if applicable
                if is_returned:
                    with ui.row().classes('mb-4'):
                        ui.badge("Returned", color='negative').props('outline')
                        ui.label(f"Returned on: {row.get('returned_date', 'N/A')}").classes("text-sm text-gray-600 ml-2")
                        if row.get('correction_date'):
                            ui.label(f"• Corrected on: {row.get('correction_date', 'N/A')}").classes("text-sm text-gray-600 ml-2")
                
                with ui.column().classes('gap-4 w-full'):
                    ui.label(f"Contract Owner: {row['manager']}").classes("text-base")
                    ui.label(f"Response Provided By: {row['response_provided_by']}").classes("text-base")
                    ui.label(f"Response Date: {row['response_date']}").classes("text-base")
                    
                    # Show previous response information if this is a returned contract
                    if is_returned and row.get('previous_response'):
                        ui.separator()
                        ui.label("Previous Response Information:").classes("text-base font-semibold text-orange-700")
                        with ui.card().classes('p-4 bg-orange-50 border border-orange-200'):
                            prev_date = row['previous_response'].get('date')
                            if prev_date:
                                if hasattr(prev_date, 'strftime'):
                                    date_str = prev_date.strftime('%Y-%m-%d')
                                else:
                                    date_str = str(prev_date)
                                ui.label(f"Previous Response Date: {date_str}").classes("text-sm")
                            ui.label(f"Previous Response: {row['previous_response'].get('response', 'N/A')}").classes("text-sm")
                            if row['previous_response'].get('has_document'):
                                ui.label("Previous Document: Available (retained if unchanged)").classes("text-sm text-green-700 font-semibold")
                            else:
                                ui.label("Previous Document: Not provided").classes("text-sm")
                        
                        if row.get('returned_reason'):
                            with ui.card().classes('p-4 bg-red-50 border border-red-200 mt-2'):
                                ui.label("Reason for Return:").classes("text-sm font-semibold text-red-700")
                                ui.label(row['returned_reason']).classes("text-sm text-red-600")
                    
                    ui.separator()
                    
                    ui.label("Current Response Details:").classes("text-base font-semibold")
                    response_text = "The contract manager has reviewed and provided feedback on this contract. "
                    if is_returned:
                        response_text += "This is a corrected response after the contract was returned. All required corrections have been addressed."
                    else:
                        response_text += "All required information has been updated as per the notification window requirements."
                    ui.label(response_text).classes("text-sm text-gray-700")
                    
                    if row.get('has_document', False):
                        ui.label("Document Available: Yes").classes("text-base font-semibold text-green-600")
                        with ui.row().classes('gap-2'):
                            ui.button("View Document", icon="description", on_click=lambda: ui.notify("Document viewer would open here", type="info")).props('color=primary')
                            ui.button("Download Document", icon="download", on_click=lambda: ui.notify("Document download would start here", type="info")).props('color=secondary')
                        if is_returned and row.get('previous_response', {}).get('has_document'):
                            ui.label("Note: Previous document is retained if unchanged").classes("text-xs text-gray-500 italic")
                    else:
                        ui.label("Document Available: No").classes("text-base font-semibold text-orange-600")
                        if is_returned and row.get('previous_response', {}).get('has_document'):
                            ui.label("Note: Previous document is retained").classes("text-xs text-gray-500 italic")
                    
                    ui.separator()
                    
                    # Show Contract Admin comments if this is a returned contract
                    if is_returned and row.get('admin_comments'):
                        ui.label("Contract Admin Comments:").classes("text-base font-semibold mt-2")
                        with ui.card().classes('p-3 bg-yellow-50 border border-yellow-200 mb-2'):
                            ui.label(row.get('admin_comments', 'No comments provided.')).classes("text-sm text-yellow-900")
                    
                    ui.separator()
                    
                    ui.label("Actions:").classes("text-base font-semibold mt-2")
                    with ui.column().classes('gap-2 w-full'):
                        ui.button("Edit Information", icon="edit", on_click=lambda: [edit_contract_info(row, dialog), dialog.close()]).props('color=secondary full-width')
                        # For returned contracts, "Process Task" routes to next workflow step
                        if is_returned:
                            ui.button("Process Task & Route", icon="forward", on_click=lambda: [complete_contract(row), dialog.close()]).props('color=positive full-width')
                        else:
                            ui.button("Complete", icon="check_circle", on_click=lambda: [complete_contract(row), dialog.close()]).props('color=positive full-width')
                        if not is_returned:  # Only show Send Back for non-returned contracts
                            ui.button("Send Back", icon="undo", on_click=lambda: [send_back_contract(row), dialog.close()]).props('color=negative full-width')
                    
                    with ui.row().classes('gap-2 justify-end w-full mt-4'):
                        ui.button("Close", on_click=dialog.close).props('flat')
            
            dialog.open()
        
        # Replace the view_response function
        view_response = view_response_with_actions
        
        # Add slot for actions column - "Response" button
        # Since NiceGUI table slots have limitations with Python callbacks,
        # we'll use a simpler approach: the button opens the response dialog
        # which contains all action options (View Response, Edit, Complete, Send Back)
        contracts_table.add_slot('body-cell-actions', '''
            <q-td :props="props">
                <q-btn 
                    label="Response" 
                    color="primary" 
                    size="sm" 
                    icon="description"
                    @click="() => {
                        const contractId = props.row.contract_id;
                        // Store in window for Python to access
                        window.pendingContractAction = contractId;
                        // Trigger event
                        window.dispatchEvent(new Event('contractActionPending'));
                    }"
                />
            </q-td>
        ''')
        
        # Initialize JavaScript bridge for contract actions
        ui.add_head_html('''
            <script>
                window.pendingContractAction = null;
                window.contractActionHandlers = [];
            </script>
        ''')
        
        # Set up event listener using timer to check for pending actions
        # Note: This uses a polling mechanism as NiceGUI table slots don't easily support
        # direct Python callbacks. In production, you might want to use a different approach
        # such as custom table implementation or API endpoints.
        pending_contract_ids = []
        
        def process_pending_actions():
            """Process any pending contract actions"""
            try:
                # Check JavaScript for pending actions
                js_code = 'window.pendingContractAction || null'
                result = ui.run_javascript(js_code)
                
                # Handle the result (might be async, so we check if it's a string or has value)
                contract_id = None
                if isinstance(result, str) and result != 'null':
                    contract_id = result
                elif hasattr(result, 'value') and result.value and result.value != 'null':
                    contract_id = result.value
                
                if contract_id and contract_id not in pending_contract_ids:
                    pending_contract_ids.append(contract_id)
                    # Clear the JavaScript variable
                    ui.run_javascript('window.pendingContractAction = null')
                    # Open the actions dialog
                    open_actions_for_contract(contract_id)
                    # Remove from pending list after a delay
                    def remove_from_pending():
                        if contract_id in pending_contract_ids:
                            pending_contract_ids.remove(contract_id)
                    ui.timer(1.0, remove_from_pending, once=True)
            except Exception:
                # Silently handle errors - the timer will keep checking
                pass
        
        # Check every 500ms for pending actions
        ui.timer(0.5, process_pending_actions)

