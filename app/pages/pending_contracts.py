from datetime import datetime, timedelta, date
import asyncio
from nicegui import ui, app, run
import io
import re
import base64
import httpx
from app.db.database import SessionLocal
from app.services.contract_service import ContractService
from app.models.contract import (
    Contract,
    ContractStatusType,
    ContractTerminationType,
    ContractUpdate,
    ContractUpdateStatus,
    User,
)
from sqlalchemy.orm import joinedload
from app.utils.navigation import get_dashboard_url
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


def _complete_pending_contract_blocking(
    contract_db_id: int,
    current_user_id,
    decision_value: str,
    end_val: str | None,
    term_doc_name: str,
    term_doc_date: str,
    term_doc_file_content: bytes | None,
    term_doc_file_name: str,
    comments: str,
    renew_has_document: bool = False,
) -> tuple[bool, str | None]:
    """Runs in background thread: upload (if Terminate+file) and DB update. Returns (success, error_message)."""
    try:
        if decision_value == "Renew":
            if not end_val or not end_val.strip():
                return (False, "End date is required for Renew.")
            try:
                new_end = datetime.strptime(end_val.replace("/", "-"), "%Y-%m-%d").date()
            except Exception:
                return (False, "Invalid end date.")
            db_ren = SessionLocal()
            try:
                upd = (
                    db_ren.query(ContractUpdate)
                    .filter(ContractUpdate.contract_id == contract_db_id)
                    .order_by(ContractUpdate.created_at.desc())
                    .first()
                )
                if not upd:
                    upd = ContractUpdate(contract_id=contract_db_id, status=ContractUpdateStatus.PENDING_REVIEW)
                    db_ren.add(upd)
                upd.decision = "Extend"
                upd.initial_expiration_date = new_end
                upd.response_provided_by_user_id = current_user_id
                upd.decision_comments = comments or ""
                upd.updated_at = datetime.utcnow()
                upd.has_document = renew_has_document
                db_ren.commit()
            finally:
                db_ren.close()
            return (True, None)
        else:
            # Terminate
            if term_doc_file_content:
                if not (term_doc_name and term_doc_date):
                    return (False, "Document name and Issue Date are required for the uploaded termination document.")
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
                        return (False, r.text or f"Request failed (HTTP {r.status_code})")
            db3 = SessionLocal()
            try:
                upd = (
                    db3.query(ContractUpdate)
                    .filter(ContractUpdate.contract_id == contract_db_id)
                    .order_by(ContractUpdate.created_at.desc())
                    .first()
                )
                if not upd:
                    upd = ContractUpdate(contract_id=contract_db_id, status=ContractUpdateStatus.PENDING_REVIEW)
                    db3.add(upd)
                upd.decision = "Terminate"
                upd.has_document = True
                upd.response_provided_by_user_id = current_user_id
                upd.decision_comments = comments or ""
                upd.updated_at = datetime.utcnow()
                db3.commit()
            finally:
                db3.close()
            return (True, None)
    except Exception as e:
        return (False, str(e))


def pending_contracts():
    # Get current logged-in user - use stored user_id first (from login)
    current_user_id = app.storage.user.get('user_id', None)
    
    # If user_id is not stored, try to look it up by username
    if not current_user_id:
        current_username = app.storage.user.get('username', None)
        try:
            db = SessionLocal()
            try:
                if current_username:
                    # Try multiple matching strategies
                    current_user = db.query(User).filter(User.email == current_username).first()
                    if not current_user:
                        current_user = db.query(User).filter(User.email.ilike(f"%{current_username}%")).first()
                    if not current_user:
                        current_user = db.query(User).filter(User.first_name.ilike(f"%{current_username}%")).first()
                    if not current_user:
                        current_user = db.query(User).filter(User.last_name.ilike(f"%{current_username}%")).first()
                    if not current_user and ' ' in current_username:
                        parts = current_username.split()
                        if len(parts) >= 2:
                            current_user = db.query(User).filter(
                                User.first_name.ilike(f"%{parts[0]}%"),
                                User.last_name.ilike(f"%{parts[-1]}%")
                            ).first()
                    
                    if current_user:
                        current_user_id = current_user.id
                        print(f"Found current user: {current_user.first_name} {current_user.last_name} (ID: {current_user_id})")
                    else:
                        print(f"Could not find user matching: {current_username}")
            finally:
                db.close()
        except Exception as e:
            print(f"Error fetching current user: {e}")
            import traceback
            traceback.print_exc()
    
    if current_user_id:
        print(f"Using stored user_id: {current_user_id}")
    # Navigation
    with ui.row().classes("max-w-6xl mx-auto mt-4"):
        with ui.link(target=get_dashboard_url()).classes('no-underline'):
            ui.button("Back to Dashboard", icon="arrow_back").props('flat color=primary')
    
    # Global variables for table and data
    contracts_table = None
    contract_rows = []
    
    # Function to handle owned/backup toggle
    
    # Fetch contracts with no documents OR awaiting termination document from database
    def fetch_pending_documents_contracts():
        """
        Fetches:
        1. Active contracts that have no documents uploaded.
        2. Contracts where manager chose Terminate but has_document=false (awaiting termination doc).
        """
        db = SessionLocal()
        try:
            contract_service = ContractService(db)
            
            # Get contracts with no documents
            contracts_no_docs, _ = contract_service.get_contracts_with_no_documents(
                skip=0,
                limit=1000
            )
            # Get contracts awaiting termination document (manager chose Terminate, saved, no doc yet)
            contracts_awaiting_term, _ = contract_service.get_contracts_awaiting_termination_document(
                skip=0,
                limit=1000
            )
            
            # Merge and deduplicate by contract id
            seen_ids = set()
            contracts = []
            for c in contracts_no_docs:
                if c.id not in seen_ids:
                    seen_ids.add(c.id)
                    contracts.append(c)
            for c in contracts_awaiting_term:
                if c.id not in seen_ids:
                    seen_ids.add(c.id)
                    contracts.append(c)
            
            print(f"Found {len(contracts)} contracts with pending documents from database ({len(contracts_no_docs)} no docs, {len(contracts_awaiting_term)} awaiting termination doc)")
            
            if not contracts:
                print("No contracts with pending documents found in database")
                return []
            
            # Map contract data to table row format
            rows = []
            for contract in contracts:
                # Get vendor info
                vendor_name = contract.vendor.vendor_name if contract.vendor else "Unknown"
                vendor_id = contract.vendor.id if contract.vendor else None
                
                # Get contract type value
                contract_type = contract.contract_type.value if hasattr(contract.contract_type, 'value') else str(contract.contract_type)
                
                # Format expiration date (end_date)
                if contract.end_date:
                    if isinstance(contract.end_date, date):
                        exp_date = contract.end_date
                        formatted_date = exp_date.strftime("%Y-%m-%d")
                        exp_timestamp = datetime.combine(exp_date, datetime.min.time()).timestamp()
                    else:
                        formatted_date = str(contract.end_date)
                        exp_timestamp = 0
                else:
                    formatted_date = "N/A"
                    exp_timestamp = 0
                
                # Determine user's role for this contract
                my_role = "N/A"
                if current_user_id:
                    if contract.contract_owner_id == current_user_id:
                        my_role = "Contract Manager"
                    elif contract.contract_owner_backup_id == current_user_id:
                        my_role = "Backup"
                    elif contract.contract_owner_manager_id == current_user_id:
                        my_role = "Owner"
                else:
                    # Simulation mode: Cycle through users to show different roles
                    all_users = db.query(User).order_by(User.id).limit(3).all()
                    if all_users:
                        user_index = (contract.id - 1) % len(all_users)
                        sim_user_id = all_users[user_index].id
                        if contract.contract_owner_id == sim_user_id:
                            my_role = "Contract Manager"
                        elif contract.contract_owner_backup_id == sim_user_id:
                            my_role = "Backup"
                        elif contract.contract_owner_manager_id == sim_user_id:
                            my_role = "Owner"
                
                row_data = {
                    "id": int(contract.id),
                    "contract_id": str(contract.contract_id or ""),
                    "vendor_id": int(vendor_id) if vendor_id else 0,
                    "vendor_name": str(vendor_name or ""),
                    "contract_type": str(contract_type or ""),
                    "description": str(contract.contract_description or ""),
                    "expiration_date": str(formatted_date),
                    "expiration_timestamp": float(exp_timestamp),
                    "status": "Pending documents",  # Display status (not from DB)
                    "my_role": str(my_role),
                }
                rows.append(row_data)
            
            print(f"Processed {len(rows)} contract rows")
            return rows
            
        except Exception as e:
            error_msg = f"Error fetching pending contracts: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            ui.notify(error_msg, type="negative")
            return []
        finally:
            db.close()

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
            "name": "status",
            "label": "Status",
            "field": "status",
            "align": "left",
        },
        {
            "name": "my_role",
            "label": "My Role",
            "field": "my_role",
            "align": "left",
            "sortable": True,
        },
    ]

    contract_columns_defaults = {
        "align": "left",
        "headerClasses": "bg-[#144c8e] text-white",
    }

    contract_rows = []
    
    # Initial fetch
    contract_rows = fetch_pending_documents_contracts()
    
    # Debug: Check if we have data
    print(f"Total contract rows fetched: {len(contract_rows)}")
    if contract_rows:
        print(f"First row sample: {contract_rows[0]}")
    else:
        ui.notify("No pending documents contracts available. All active contracts have documents uploaded.", type="info")
    
    # Main container
    with ui.element("div").classes("max-w-6xl mt-8 mx-auto w-full"):
        # Section header
        with ui.row().classes('items-center justify-between ml-4 mb-4 w-full'):
            with ui.row().classes('items-center gap-2'):
                ui.icon('edit', color='orange').style('font-size: 32px')
                ui.label("Pending Documents").classes("text-h5 font-bold")
        
        # Description row
        with ui.row().classes('ml-4 mb-4 w-full'):
            ui.label("Contracts missing required documents").classes(
                "text-sm text-gray-500"
            )
        
        # Count label row
        with ui.row().classes('ml-4 mb-2'):
            count_label = ui.label(f"Total: {len(contract_rows)} contracts").classes("text-sm text-gray-500")
        
        # Define search functions first
        def filter_contracts():
            # Show all contracts regardless of role
            base_rows = contract_rows
            
            search_term = (search_input.value or "").lower()
            if not search_term:
                contracts_table.rows = base_rows
            else:
                filtered = [
                    row for row in base_rows
                    if search_term in (row['contract_id'] or "").lower()
                    or search_term in (row['vendor_name'] or "").lower()
                    or search_term in (row['contract_type'] or "").lower()
                    or search_term in (row['description'] or "").lower()
                    or search_term in (row['my_role'] or "").lower()
                ]
                contracts_table.rows = filtered
            contracts_table.update()
        
        def clear_search():
            search_input.value = ""
            filter_contracts()  # Use filter_contracts to respect current role
        
        # Search input for filtering contracts (above the table)
        with ui.row().classes('w-full ml-4 mr-4 mb-6 gap-2 px-2'):
            search_input = ui.input(placeholder='Search by Contract ID, Vendor, Type, Description, or My Role...').classes(
                'flex-1'
            ).props('outlined dense clearable')
            with search_input.add_slot('prepend'):
                ui.icon('search').classes('text-gray-400')
            ui.button(icon='search', on_click=filter_contracts).props('color=primary')
            ui.button(icon='clear', on_click=clear_search).props('color=secondary')
        
        # Show message if no data
        if not contract_rows:
            with ui.card().classes("w-full p-6"):
                ui.label("No pending documents contracts found").classes("text-lg font-bold text-gray-500")
                ui.label("All active contracts have documents uploaded, or there are no active contracts.").classes("text-sm text-gray-400 mt-2")
        
        # Create table after search bar (showing all contracts)
        initial_rows = contract_rows
        print(f"Creating table with {len(initial_rows)} rows")
        
        contracts_table = ui.table(
            columns=contract_columns,
            column_defaults=contract_columns_defaults,
            rows=initial_rows,
            pagination=10,
            row_key="id"
        ).classes("w-full").props("flat bordered").classes(
            "contracts-table shadow-lg rounded-lg overflow-hidden"
        )
        
        # Force update if we have data
        if initial_rows:
            contracts_table.update()
        
        # Generate button (moved from header to after table)
        ui.button("Generate", icon="description", on_click=lambda: open_generate_dialog()).props('color=primary').classes('ml-4 mt-4')
        
        search_input.on_value_change(filter_contracts)
        
        # Add custom CSS for visual highlighting and toggle styling
        ui.add_css("""
            .contracts-table thead tr {
                background-color: #144c8e !important;
            }
            .contracts-table tbody tr {
                background-color: white !important;
            }
        """)
        
        # Add slot for contract ID with clickable link (links to contract info)
        contracts_table.add_slot('body-cell-contract_id', '''
            <q-td :props="props">
                <a :href="'/contract-info/' + props.row.id" class="text-blue-600 hover:text-blue-800 underline cursor-pointer">
                    {{ props.value }}
                </a>
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
        
        # Add slot for status column: clickable to open Contract Decision pop-up
        contracts_table.add_slot('body-cell-status', '''
            <q-td :props="props">
                <q-btn
                    flat
                    dense
                    no-caps
                    class="text-orange-600 font-semibold cursor-pointer"
                    @click="$parent.$emit('status_click', props.row)"
                >
                    <q-icon name="pending" color="orange" size="sm" class="q-mr-xs" />
                    {{ props.value }}
                </q-btn>
            </q-td>
        ''')
        
        # Add slot for My Role column with badge styling
        contracts_table.add_slot('body-cell-my_role', '''
            <q-td :props="props">
                <q-badge 
                    v-if="props.value && props.value !== 'N/A'"
                    :color="props.value === 'Owner' ? 'primary' : (props.value === 'Contract Manager' ? 'blue' : 'orange')" 
                    :label="props.value"
                />
                <span v-else class="text-gray-500">{{ props.value || 'N/A' }}</span>
            </q-td>
        ''')

        # --- Contract Decision pop-up (when user clicks status in Pending Documents list) ---
        selected_contract = {}

        with ui.dialog().props("max-width=640px") as contract_decision_dialog, ui.card().classes("w-full max-w-3xl max-h-[90vh] overflow-y-auto p-6"):
            ui.label("Contract Decision").classes("text-h5 mb-4 text-blue-600 font-bold")
            dialog_content = ui.column().classes("w-full gap-4")

        def populate_dialog_content():
            dialog_content.clear()
            contract_db_id = selected_contract.get("id") or selected_contract.get("contract_db_id")
            contract_obj = None
            update = None
            acted_by_name = "N/A"
            existing_comments = ""
            try:
                db2 = SessionLocal()
                try:
                    contract_obj = (
                        db2.query(Contract)
                        .options(
                            joinedload(Contract.documents),
                            joinedload(Contract.termination_documents),
                            joinedload(Contract.contract_owner),
                            joinedload(Contract.contract_owner_backup),
                            joinedload(Contract.contract_owner_manager),
                        )
                        .filter(Contract.id == contract_db_id)
                        .first()
                    )
                    if contract_obj:
                        owner_name = f"{contract_obj.contract_owner.first_name} {contract_obj.contract_owner.last_name}" if contract_obj.contract_owner else "N/A"
                        backup_name = f"{contract_obj.contract_owner_backup.first_name} {contract_obj.contract_owner_backup.last_name}" if contract_obj.contract_owner_backup else "N/A"
                        manager_name = f"{contract_obj.contract_owner_manager.first_name} {contract_obj.contract_owner_manager.last_name}" if contract_obj.contract_owner_manager else "N/A"
                        acted_by_name = f"Contract Manager: {owner_name}, Backup: {backup_name}, Owner: {manager_name}"
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
                    if update and getattr(update, "decision_comments", None):
                        existing_comments = update.decision_comments or ""
                    # Parse planned doc name/date from decision_comments if saved earlier
                    planned_doc_name, planned_doc_date = "", ""
                    if update and update.decision_comments:
                        m = re.search(r'\[Planned termination doc: ([^]]*), date: ([^]]*)\]', update.decision_comments)
                        if m:
                            planned_doc_name = m.group(1).strip() if m.group(1) != "(not set)" else ""
                            planned_doc_date = m.group(2).strip() if m.group(2) != "(not set)" else ""
                            # Normalize date to YYYY-MM-DD for type=date input
                            if planned_doc_date and re.match(r"\d{4}-\d{2}-\d{2}", planned_doc_date):
                                pass
                            elif planned_doc_date:
                                try:
                                    from datetime import datetime as _dt
                                    parsed = _dt.strptime(planned_doc_date.replace("/", "-").strip()[:10], "%Y-%m-%d")
                                    planned_doc_date = parsed.strftime("%Y-%m-%d")
                                except Exception:
                                    pass
                            # Show comments without the planned-doc line in the textarea
                            existing_comments = re.sub(r'\s*\[Planned termination doc: [^]]*, date: [^]]*\]\s*', '\n', existing_comments).strip()
                    prev_decision = (update.decision if update and update.decision else None) or selected_contract.get("decision") or "Terminate"
                    if prev_decision == "Extend":
                        prev_decision = "Renew"
                finally:
                    db2.close()
            except Exception as e:
                print(f"Error loading contract for dialog: {e}")
                prev_decision = "Terminate"

            with dialog_content:
                # Display Status of Pending Documents within the pop-up
                with ui.row().classes("mb-2 items-center gap-2"):
                    ui.label("Status:").classes("text-sm font-medium text-gray-600")
                    ui.badge("Pending Documents", color="orange").classes("text-sm font-semibold")

                # Contract summary
                with ui.row().classes("mb-4 p-4 bg-gray-50 rounded-lg w-full"):
                    with ui.column().classes("gap-1"):
                        ui.label(f"Contract ID: {selected_contract.get('contract_id', 'N/A')}").classes("font-bold text-lg")
                        ui.label(f"Vendor: {selected_contract.get('vendor_name', 'N/A')}").classes("text-gray-600")
                        ui.label(f"Expiration Date: {selected_contract.get('expiration_date', 'N/A')}").classes("text-gray-600")
                        ui.label(f"Action taken by: {acted_by_name}").classes("text-gray-600 text-sm")

                # Decision section (renamed from Termination Decision)
                ui.label("Decision").classes("text-lg font-bold")
                decision_options = ["Terminate", "Renew"]
                decision_select = ui.select(
                    options=decision_options,
                    value=prev_decision if prev_decision in decision_options else "Terminate"
                ).classes("w-full").props("outlined dense")

                end_date_container = ui.column().classes("w-full")
                with end_date_container:
                    end_date_input = ui.input("End Date (required for Renew)", value=selected_contract.get("expiration_date") or "").props("type=date outlined dense").classes("w-full")
                    def _base_date():
                        raw = (end_date_input.value or "").strip() or (selected_contract.get("expiration_date") or "")
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
                        set_complete_state()
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
                        set_complete_state()

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

                # Documents & Comments: view uploaded docs and add comments (same comment box)
                ui.label("Documents & Comments").classes("text-lg font-bold mt-2")
                with ui.card().classes("p-4 bg-white border w-full"):
                    ui.label("Comments (Contract Manager / Backup / Owner can add comments below):").classes("font-medium")
                    comments_input = ui.textarea(value=existing_comments).classes("w-full").props("outlined")
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

                # Complete, Save, Cancel
                with ui.row().classes("gap-3 justify-end mt-4 w-full"):
                    complete_btn = ui.button("Complete", icon="check_circle").props("color=positive")
                    save_btn = ui.button("Save", icon="save").props("color=primary")
                    ui.button("Cancel", icon="cancel", on_click=contract_decision_dialog.close).props("flat color=grey")
                with ui.row().classes("gap-2 items-center mt-2") as loading_row:
                    ui.spinner(size="sm", color="primary")
                    ui.label("Completing…")
                loading_row.set_visibility(False)

                def can_complete():
                    if decision_select.value == "Renew":
                        return bool((end_date_input.value or "").strip())
                    # Terminate: need at least one termination doc (existing or just uploaded)
                    has_existing = contract_obj and contract_obj.termination_documents and len(contract_obj.termination_documents) > 0
                    has_upload = term_doc_upload_ref.get("content")
                    return has_existing or bool(has_upload)

                def set_complete_state():
                    # Complete is always clickable; when Terminate and no doc it appears gray and click shows message
                    if can_complete():
                        complete_btn.props(remove="color=grey")
                        complete_btn.props("color=positive")
                    else:
                        complete_btn.props(remove="color=positive")
                        complete_btn.props("color=grey")

                def do_complete():
                    if not can_complete():
                        ui.notify("Please upload the Termination Document", type="negative")
                        return
                    decision_value = decision_select.value
                    if decision_value == "Renew":
                        end_val = (end_date_input.value or "").strip()
                        if not end_val:
                            ui.notify("End date is required for Renew.", type="negative")
                            return
                        try:
                            datetime.strptime(end_val.replace("/", "-"), "%Y-%m-%d").date()
                        except Exception:
                            ui.notify("Invalid end date.", type="negative")
                            return
                    else:
                        # Terminate with upload: require name and date
                        has_upload = term_doc_upload_ref.get("content")
                        if has_upload:
                            tname = (term_doc_name_input.value or "").strip()
                            tdate = (term_doc_date_input.value or "").strip()
                            if not tname or not tdate:
                                ui.notify("Document name and Issue Date are required for the uploaded termination document.", type="negative")
                                return

                    async def run_complete():
                        loading_row.set_visibility(True)
                        complete_btn.disable()
                        save_btn.disable()
                        decision_value = decision_select.value
                        end_val = (end_date_input.value or "").strip() if decision_value == "Renew" else None
                        term_doc_name = (term_doc_name_input.value or "").strip()
                        term_doc_date = (term_doc_date_input.value or "").strip()
                        comments = (comments_input.value or "").strip()
                        term_doc_content = term_doc_upload_ref.get("content")
                        term_doc_file_name = term_doc_upload_ref.get("name") or "document.pdf"
                        renew_has_document = bool(
                            term_doc_upload_ref.get("content") or (contract_obj and contract_obj.documents)
                        )
                        try:
                            result = await run.io_bound(
                                _complete_pending_contract_blocking,
                                contract_db_id,
                                current_user_id,
                                decision_value,
                                end_val,
                                term_doc_name,
                                term_doc_date,
                                term_doc_content,
                                term_doc_file_name,
                                comments,
                                renew_has_document,
                            )
                        except Exception as e:
                            result = (False, str(e))
                        # Run UI updates in the dialog context so slot stack is available (background task loses it)
                        with contract_decision_dialog:
                            loading_row.set_visibility(False)
                            complete_btn.enable()
                            save_btn.enable()
                            if result[0]:
                                ui.notify(
                                    "Contract sent for admin review (renew)." if decision_value == "Renew" else "Contract sent for admin review (terminate).",
                                    type="positive",
                                )
                                contract_decision_dialog.close()
                                contract_rows[:] = fetch_pending_documents_contracts()
                                contracts_table.rows = contract_rows
                                contracts_table.update()
                                count_label.text = f"Total: {len(contract_rows)} contracts"
                            else:
                                ui.notify(result[1] or "Request failed", type="negative")

                    if not hasattr(contract_decision_dialog, "_complete_tasks"):
                        contract_decision_dialog._complete_tasks = set()
                    complete_task = asyncio.create_task(run_complete())
                    contract_decision_dialog._complete_tasks.add(complete_task)
                    complete_task.add_done_callback(lambda t: contract_decision_dialog._complete_tasks.discard(t))

                def do_save():
                    """Save progress without completing. Do not set has_document from upload; stay in Pending Documents until Complete."""
                    try:
                        db_save = SessionLocal()
                        try:
                            upd = (
                                db_save.query(ContractUpdate)
                                .filter(ContractUpdate.contract_id == contract_db_id)
                                .order_by(ContractUpdate.created_at.desc())
                                .first()
                            )
                            if not upd:
                                upd = ContractUpdate(contract_id=contract_db_id, status=ContractUpdateStatus.PENDING_REVIEW)
                                db_save.add(upd)
                            upd.decision = "Extend" if decision_select.value == "Renew" else "Terminate"
                            comments = (comments_input.value or "").strip()
                            if decision_select.value == "Terminate":
                                tname = (term_doc_name_input.value or "").strip()
                                tdate = (term_doc_date_input.value or "").strip()
                                if tname or tdate:
                                    comments = (comments + "\n" if comments else "") + f"[Planned termination doc: {tname or '(not set)'}, date: {tdate or '(not set)'}]"
                            upd.decision_comments = comments
                            if decision_select.value == "Renew":
                                end_val = (end_date_input.value or "").strip()
                                if end_val:
                                    upd.initial_expiration_date = datetime.strptime(end_val.replace("/", "-"), "%Y-%m-%d").date()
                            # Do not set has_document from current upload; only Complete sets it. Stay in Pending Documents.
                            upd.has_document = bool(contract_obj and contract_obj.termination_documents)
                            upd.updated_at = datetime.utcnow()
                            db_save.commit()
                            ui.notify("Progress saved", type="positive")
                            contract_rows[:] = fetch_pending_documents_contracts()
                            contracts_table.rows = contract_rows
                            contracts_table.update()
                            count_label.text = f"Total: {len(contract_rows)} contracts"
                        finally:
                            db_save.close()
                    except Exception as e:
                        ui.notify(f"Error saving: {e}", type="negative")
                    contract_decision_dialog.close()

                complete_btn.on_click(do_complete)
                save_btn.on_click(do_save)
                set_complete_state()
                decision_select.on_value_change(lambda e: set_complete_state())
                end_date_input.on_value_change(lambda e: set_complete_state())
                term_doc_name_input.on_value_change(lambda e: set_complete_state())
                term_doc_date_input.on_value_change(lambda e: set_complete_state())

        def open_contract_decision_dialog(row: dict):
            selected_contract.clear()
            selected_contract["id"] = row.get("id")
            selected_contract["contract_id"] = row.get("contract_id", "")
            selected_contract["vendor_name"] = row.get("vendor_name", "N/A")
            selected_contract["expiration_date"] = row.get("expiration_date", "N/A")
            selected_contract["decision"] = row.get("decision")
            populate_dialog_content()
            contract_decision_dialog.open()

        def on_status_click(e):
            try:
                row = e.args
                if isinstance(row, dict) and (row.get("id") is not None or row.get("contract_id")):
                    open_contract_decision_dialog(row)
            except Exception as ex:
                ui.notify(f"Could not open Contract Decision: {ex}", type="negative")

        contracts_table.on("status_click", on_status_click)

        # Function to generate Excel report
        def open_generate_dialog():
            """Open dialog for date range selection and report generation"""
            with ui.dialog() as dialog, ui.card().classes('p-6 w-full max-w-md'):
                ui.label("Generate Pending Documents Report").classes("text-h6 font-bold mb-4")
                
                with ui.column().classes('gap-4 w-full'):
                    ui.label("Select date range for pending documents:").classes("text-sm text-gray-600")
                    
                    start_date_input = ui.input("Start Date", placeholder="YYYY-MM-DD").props('type=date').classes('w-full')
                    end_date_input = ui.input("End Date", placeholder="YYYY-MM-DD").props('type=date').classes('w-full')
                    
                    # Set default dates (last 6 months)
                    today = datetime.now()
                    default_start = (today - timedelta(days=180)).strftime("%Y-%m-%d")
                    default_end = today.strftime("%Y-%m-%d")
                    start_date_input.value = default_start
                    end_date_input.value = default_end
                    
                    ui.label("The report will include all contracts with pending documents.").classes("text-xs text-gray-500 italic")
                    
                    with ui.row().classes('gap-2 justify-end w-full mt-4'):
                        ui.button("Cancel", on_click=dialog.close).props('flat')
                        ui.button("Generate & Download", icon="download", 
                                 on_click=lambda: generate_excel_report(start_date_input.value, end_date_input.value, dialog)).props('color=primary')
                
                dialog.open()
        
        def generate_excel_report(start_date_str, end_date_str, dialog):
            """Generate Excel report for pending contracts"""
            try:
                if not PANDAS_AVAILABLE:
                    ui.notify("Excel export requires pandas library. Please install it: pip install pandas openpyxl", type="negative")
                    dialog.close()
                    return
                
                if not contract_rows:
                    ui.notify("No pending contracts available for export", type="warning")
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
                        "My Role": contract.get('my_role', ''),
                    })
                
                # Create DataFrame
                df = pd.DataFrame(report_data)
                
                # Create Excel file in memory
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Pending Documents')
                    
                    # Get the worksheet
                    worksheet = writer.sheets['Pending Documents']
                    
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
                filename = f"Pending_Documents_Report_{start_date_str}_to_{end_date_str}.xlsx"
                
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
