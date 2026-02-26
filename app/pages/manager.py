from datetime import datetime, timedelta, date
import requests
from nicegui import ui, app
from app.utils.vendor_lookup import get_vendor_id_by_name
import re


def manager():
    # Get current logged-in user
    current_username = app.storage.user.get('username', None)
    current_user_id = None
    current_user_name = None
    
    # Fetch current user from database
    try:
        from app.db.database import SessionLocal
        from app.models.contract import User
        db = SessionLocal()
        try:
            if current_username:
                # Try to find user by email or username
                current_user = db.query(User).filter(
                    (User.email == current_username) | (User.first_name.ilike(f"%{current_username}%"))
                ).first()
                if current_user:
                    current_user_id = current_user.id
                    current_user_name = f"{current_user.first_name} {current_user.last_name}"
        finally:
            db.close()
    except Exception as e:
        print(f"Error fetching current user: {e}")
    
    # Global variables for table and data
    contracts_table = None
    contract_rows = []
    
    # Fetch active contracts count from database
    active_contracts_count = 0
    try:
        from app.db.database import SessionLocal
        from app.services.contract_service import ContractService
        from app.models.contract import ContractStatusType
        db = SessionLocal()
        try:
            contract_service = ContractService(db)
            _, active_contracts_count = contract_service.search_and_filter_contracts(
                skip=0,
                limit=1,
                status=ContractStatusType.ACTIVE,
                search=None,
                contract_type=None,
                department=None,
                owner_id=None,
                vendor_id=None,
                expiring_soon=None
            )
        finally:
            db.close()
    except Exception as e:
        print(f"Error fetching active contracts count: {e}")
        active_contracts_count = 0
    
    
    # Single container: cards + Contracts Requiring Attention table (same as admin view, table visible on load)
    # Use max-w-7xl (1280px) for wider table - was max-w-6xl (1152px)
    with ui.column().classes("max-w-7xl mx-auto w-full gap-0 min-w-0"):
        # Quick Stats Cards - Only 3 cards as requested
        with ui.row().classes(
            "grid grid-cols-1 md:grid-cols-3 mt-8 gap-6 w-full"
        ):
            # Card 1: Active Contracts
            with ui.link(target='/active-contracts').classes('no-underline w-full').style('text-decoration: none !important;'):
                with ui.card().classes("w-full cursor-pointer hover:bg-gray-50 transition-colors shadow-lg").props('flat'):
                    with ui.row().classes('items-center gap-2'):
                        ui.icon('article', color='primary').style('font-size: 28px')
                        ui.label("Active Contracts").classes("text-lg font-bold")
                    ui.label("Currently active contracts").classes("text-sm text-gray-500 mt-2")
                    ui.label(str(active_contracts_count)).classes("text-2xl font-medium text-primary mt-2")
            
            # Card 2: Pending Documents
            with ui.link(target='/pending-contracts').classes('no-underline w-full').style('text-decoration: none !important;'):
                with ui.card().classes("w-full cursor-pointer hover:bg-gray-50 transition-colors shadow-lg").props('flat'):
                    with ui.row().classes('items-center gap-2'):
                        ui.icon('edit', color='primary').style('font-size: 28px')
                        ui.label("Pending Documents").classes("text-lg font-bold")
                    ui.label("Contracts missing documents").classes("text-sm text-gray-500 mt-2")
                    ui.label("12").classes("text-2xl font-medium text-primary mt-2")
            
            # Card 3: Contract Updates
            with ui.link(target='/contract-updates').classes('no-underline w-full').style('text-decoration: none !important;'):
                with ui.card().classes("w-full cursor-pointer hover:bg-gray-50 transition-colors shadow-lg").props('flat'):
                    with ui.row().classes('items-center gap-2'):
                        ui.icon('update', color='primary').style('font-size: 28px')
                        ui.label("Contract Updates").classes("text-lg font-bold")
                    ui.label("Review manager responses and updates").classes("text-sm text-gray-500 mt-2")
                    ui.label("15").classes("text-2xl font-medium text-primary mt-2")

        

    
    # ===== NEW SECTION: Contracts Requiring Attention =====
    
    def get_contracts_requiring_attention():
        """
        Fetch contracts that have reached their notification window
        for the current logged-in user (as Contract Manager or Backup).
        """
        if not current_user_id:
            print("No current user found, returning empty list")
            return []
        
        today = date.today()
        rows = []
        
        try:
            from app.db.database import SessionLocal
            from app.services.contract_service import ContractService
            from app.models.contract import ContractStatusType, Contract, ExpirationNoticePeriodType, ContractUpdate, ContractUpdateStatus
            from sqlalchemy import or_, and_
            from sqlalchemy.orm import joinedload
            
            db = SessionLocal()
            try:
                # Exclude contracts where manager already acted (sent for review or completed).
                # Use ANY ContractUpdate for this contract, not just PENDING_REVIEW, so that
                # after admin completes the review (status -> COMPLETED) the contract stays out.
                acted_contract_ids = [
                    r[0] for r in db.query(ContractUpdate.contract_id)
                    .distinct()
                    .all()
                ]
                # Get all active contracts where user is owner or backup
                contracts = db.query(Contract).options(
                    joinedload(Contract.vendor),
                    joinedload(Contract.contract_owner),
                    joinedload(Contract.contract_owner_backup)
                ).filter(
                    Contract.status == ContractStatusType.ACTIVE,
                    or_(
                        Contract.contract_owner_id == current_user_id,
                        Contract.contract_owner_backup_id == current_user_id
                    )
                ).all()
                
                # Filter contracts that have reached notification window (exclude those sent to Pending Documents)
                contracts_in_window = []
                for contract in contracts:
                    if not contract.end_date:
                        continue
                    if contract.id in acted_contract_ids:
                        continue  # Manager already acted - in Pending Documents or Pending Reviews
                    
                    # Parse expiration notice frequency to get days
                    notice_days = 30  # Default
                    if contract.expiration_notice_frequency:
                        freq_str = contract.expiration_notice_frequency.value if hasattr(contract.expiration_notice_frequency, 'value') else str(contract.expiration_notice_frequency)
                        # Extract number from strings like "30 days", "15 days", etc.
                        match = re.search(r'(\d+)', freq_str)
                        if match:
                            notice_days = int(match.group(1))
                    
                    # Calculate notification window start date
                    notification_window_date = contract.end_date - timedelta(days=notice_days)
                    
                    # Check if notification window has been reached
                    if today >= notification_window_date:
                        contracts_in_window.append(contract)
                
                # Build rows
                for contract in contracts_in_window:
                    # Determine user's role for this contract
                    if contract.contract_owner_id == current_user_id:
                        my_role = "Contract Manager"
                        role_color = "blue"
                        role_class = "text-blue-700"
                    elif contract.contract_owner_backup_id == current_user_id:
                        my_role = "Backup"
                        role_color = "yellow"
                        role_class = "text-yellow-700"
                    else:
                        continue  # Shouldn't happen, but skip just in case
                    
                    # Calculate days until/after expiration
                    days_diff = (contract.end_date - today).days
                    
                    # Calculate status and visual indicators
                    if days_diff < 0:
                        # Past due - RED
                        status = f"{abs(days_diff)} days past due"
                        status_class = "expired"
                        row_class = "bg-red-50"
                    else:
                        # Approaching expiration - WARNING
                        status = f"{days_diff} days remaining"
                        status_class = "warning"
                        row_class = "bg-yellow-50"
                    
                    # Get vendor info
                    vendor_name = contract.vendor.vendor_name if contract.vendor else "Unknown"
                    vendor_id = contract.vendor.id if contract.vendor else None
                    
                    # Get contract type value
                    contract_type = contract.contract_type.value if hasattr(contract.contract_type, 'value') else str(contract.contract_type)
                    
                    # Contract owner (Manager) name - same as admin mode table
                    manager_name = f"{contract.contract_owner.first_name} {contract.contract_owner.last_name}" if contract.contract_owner else "Unknown"
                    
                    rows.append({
                        "id": contract.id,  # Database ID for linking
                        "contract_id": contract.contract_id,
                        "vendor_name": vendor_name,
                        "vendor_id": vendor_id,
                        "contract_type": contract_type,
                        "description": contract.contract_description,
                        "expiration_date": contract.end_date.strftime("%Y-%m-%d"),
                        "expiration_timestamp": datetime.combine(contract.end_date, datetime.min.time()).timestamp(),
                        "status": status,
                        "status_class": status_class,
                        "row_class": row_class,
                        "manager": manager_name,
                        "my_role": my_role,
                        "role_color": role_color,
                        "role_class": role_class,
                    })
                
                print(f"Found {len(rows)} contracts requiring attention for user {current_user_name}")
                return rows
                
            finally:
                db.close()
        except Exception as e:
            print(f"Error fetching contracts requiring attention: {e}")
            import traceback
            traceback.print_exc()
            return []

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
            "name": "manager",
            "label": "Manager",
            "field": "manager",
            "align": "left",
            "sortable": True,
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

    contract_rows = get_contracts_requiring_attention()
    
    # Table section: inside card container to match top cards, visible when manager page loads
    with ui.card().classes("mt-8 w-full min-w-0 shadow-lg max-w-7xl mx-auto").props('flat'):
        # Section header - left-aligned with table
        with ui.row().classes('items-center justify-start mb-4 w-full'):
            with ui.row().classes('items-center gap-2'):
                ui.icon('warning', color='orange').style('font-size: 32px')
                ui.label("Contracts Requiring Attention").classes("text-h5 font-bold")
        
        # Description row - left-aligned with table
        with ui.row().classes('mb-4 w-full justify-start'):
            ui.label("Contracts approaching or past their expiration date").classes(
                "text-sm text-gray-500"
            )
        
        # Role filter dropdown - left-aligned with table
        role_filter = None
        with ui.row().classes('w-full mb-4 gap-4 justify-start'):
            with ui.column().classes('flex-1 min-w-[200px]'):
                ui.label("Filter by Role:").classes("text-sm font-medium mb-1")
                role_filter = ui.select(
                    options=['All', 'Contract Manager', 'Backup'],
                    value='All',
                    on_change=lambda e: filter_contracts()
                ).classes('w-full').props('outlined dense')
        
        # Define search and filter functions
        def filter_contracts():
            # Start with all contracts
            base_rows = contract_rows
            
            # Apply role filter
            if role_filter.value and role_filter.value != 'All':
                if role_filter.value == 'Contract Manager':
                    base_rows = [row for row in base_rows if row.get('my_role') == 'Contract Manager']
                elif role_filter.value == 'Backup':
                    base_rows = [row for row in base_rows if row.get('my_role') == 'Backup']
            
            # Apply search filter (include Manager like admin mode)
            search_term = (search_input.value or "").lower()
            if search_term:
                filtered = [
                    row for row in base_rows
                    if search_term in (row['contract_id'] or "").lower()
                    or search_term in (row['vendor_name'] or "").lower()
                    or search_term in (row['contract_type'] or "").lower()
                    or search_term in (row['description'] or "").lower()
                    or search_term in (row.get('manager', '') or "").lower()
                    or search_term in (row.get('my_role', '') or "").lower()
                ]
                base_rows = filtered
            
            # Update table
            if base_rows:
                contracts_table.rows = base_rows
                contracts_table.visible = True
                empty_state_container.visible = False
            else:
                contracts_table.visible = False
                empty_state_container.visible = True
            
            contracts_table.update()
        
        def clear_search():
            search_input.value = ""
            role_filter.value = 'All'
            filter_contracts()
        
        # Search input for filtering contracts (above the table) - left-aligned with table
        with ui.row().classes('w-full mb-6 gap-2 justify-start'):
            search_input = ui.input(placeholder='Search by Contract ID, Vendor, Type, Description, or Manager...').classes(
                'flex-1'
            ).props('outlined dense clearable')
            with search_input.add_slot('prepend'):
                ui.icon('search').classes('text-gray-400')
            ui.button(icon='search', on_click=filter_contracts).props('color=primary')
            ui.button(icon='clear', on_click=clear_search).props('color=secondary')
        
        # Empty state container (initially hidden)
        empty_state_container = ui.element("div").classes("w-full p-8 text-center")
        empty_state_container.visible = False
        with empty_state_container:
            ui.icon('info', size='48px', color='gray').classes('mb-4')
            ui.label("No contracts requiring attention").classes("text-xl font-semibold text-gray-600 mb-2")
            ui.label("You currently have no contracts that have reached their notification window.").classes("text-gray-500")
        
        # Create table after search bar - wrap in overflow container to prevent right-side clipping
        initial_rows = contract_rows if contract_rows else []
        with ui.element("div").classes("w-full overflow-x-auto min-w-0"):
            contracts_table = ui.table(
                columns=contract_columns,
                column_defaults=contract_columns_defaults,
                rows=initial_rows,
                pagination=10,
                row_key="contract_id"
            ).classes("w-full min-w-[800px]").props("flat bordered").classes(
                "contracts-table shadow-lg rounded-lg overflow-hidden"
            )
        
        # Show empty state if no contracts
        if not initial_rows:
            contracts_table.visible = False
            empty_state_container.visible = True
        
        search_input.on_value_change(filter_contracts)
        
        # Add custom CSS for visual highlighting of expired contracts and toggle styling
        ui.add_css("""
            .contracts-table thead tr {
                background-color: #144c8e !important;
            }
            .contracts-table tbody tr:has(td:contains("Termination Pending")) {
                background-color: #fed7aa !important;
                cursor: pointer;
            }
            .contracts-table tbody tr:has(td:contains("past due")) {
                background-color: #fee2e2 !important;
                cursor: pointer;
            }
            .contracts-table tbody tr:has(td:contains("remaining")) {
                background-color: #fef3c7 !important;
                cursor: pointer;
            }
            .contracts-table tbody tr:hover {
                opacity: 0.8;
            }
        """)
        
        # Add slot for contract ID with clickable link
        contracts_table.add_slot('body-cell-contract_id', '''
            <q-td :props="props">
                <a :href="'/contract-info/' + props.row.id" class="text-blue-600 hover:text-blue-800 underline cursor-pointer font-semibold">
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
        
        # Add slot for My Role column with color coding
        contracts_table.add_slot('body-cell-my_role', '''
            <q-td :props="props">
                <div v-if="props.row.my_role === 'Contract Manager'" class="flex items-center gap-2">
                    <q-badge color="blue" :label="props.value" class="font-semibold" />
                </div>
                <div v-else-if="props.row.my_role === 'Backup'" class="flex items-center gap-2">
                    <q-badge color="yellow" :label="props.value" text-color="black" class="font-semibold" />
                </div>
                <div v-else class="text-gray-600">{{ props.value }}</div>
            </q-td>
        ''')
        
        # Add slot for status column - clickable to open Contract Decision (Extend/Terminate) modal
        def on_status_click(e):
            try:
                row = e.args
                if isinstance(row, dict) and row.get("id") is not None:
                    open_contract_dialog(row)
            except Exception as ex:
                ui.notify(f"Could not open Contract Decision dialog: {ex}", type="negative")

        contracts_table.on("status_click", on_status_click)

        contracts_table.add_slot('body-cell-status', '''
            <q-td :props="props">
                <q-btn
                    flat
                    no-caps
                    dense
                    :icon="props.value.includes('past due') ? 'error' : (props.value.includes('Termination Pending') ? 'pending' : 'warning')"
                    :color="props.value.includes('past due') ? 'red' : 'orange'"
                    :label="props.value"
                    class="font-semibold cursor-pointer"
                    style="text-transform:none;"
                    @click="$parent.$emit('status_click', props.row)"
                />
            </q-td>
        ''')
        
        # Contract Decision pop-up (same as pending_contracts.py - when user clicks status)
        selected_contract = {}

        with ui.dialog().props("max-width=640px") as contract_decision_dialog, ui.card().classes("w-full max-w-3xl max-h-[90vh] overflow-y-auto p-6"):
            ui.label("Contract Decision").classes("text-h5 mb-4 text-blue-600 font-bold")
            dialog_content = ui.column().classes("w-full gap-4")

        def populate_dialog_content():
            from app.db.database import SessionLocal
            from app.models.contract import Contract, ContractUpdate, User
            from sqlalchemy.orm import joinedload
            import httpx

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
                    prev_decision = (update.decision if update and update.decision else None) or selected_contract.get("decision") or "Terminate"
                    if prev_decision == "Extend":
                        prev_decision = "Renew"
                finally:
                    db2.close()
            except Exception as e:
                print(f"Error loading contract for dialog: {e}")
                prev_decision = "Terminate"

            status_label = selected_contract.get("status", "Requiring attention")
            status_color = "red" if "past due" in str(status_label).lower() else "orange"

            with dialog_content:
                # Display Status within the pop-up (same as pending_contracts)
                with ui.row().classes("mb-2 items-center gap-2"):
                    ui.label("Status:").classes("text-sm font-medium text-gray-600")
                    ui.badge(status_label, color=status_color).classes("text-sm font-semibold")

                # Contract summary
                with ui.row().classes("mb-4 p-4 bg-gray-50 rounded-lg w-full"):
                    with ui.column().classes("gap-1"):
                        ui.label(f"Contract ID: {selected_contract.get('contract_id', 'N/A')}").classes("font-bold text-lg")
                        ui.label(f"Vendor: {selected_contract.get('vendor_name', 'N/A')}").classes("text-gray-600")
                        ui.label(f"Expiration Date: {selected_contract.get('expiration_date', 'N/A')}").classes("text-gray-600")
                        ui.label(f"Action taken by: {acted_by_name}").classes("text-gray-600 text-sm")

                # Decision section
                ui.label("Decision").classes("text-lg font-bold")
                decision_options = ["Terminate", "Renew"]
                decision_select = ui.select(
                    options=decision_options,
                    value=prev_decision if prev_decision in decision_options else "Terminate"
                ).classes("w-full").props("outlined dense")

                end_date_container = ui.column().classes("w-full")
                with end_date_container:
                    end_date_input = ui.input("End Date (required for Renew)", value=selected_contract.get("expiration_date") or "").props("type=date outlined dense").classes("w-full")

                term_doc_container = ui.column().classes("w-full")
                with term_doc_container:
                    ui.label("Termination Document (required for Terminate). Upload below if missing.").classes("text-sm font-medium")
                    term_doc_upload_ref = {"name": None, "content": None}
                    term_doc_name_input = ui.input("Document name", placeholder="e.g. Termination letter").props("outlined dense").classes("w-full")
                    term_doc_date_input = ui.input("Issue Date", value="").props("type=date outlined dense").classes("w-full")

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

                # Documents & Comments
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

                # Complete, Save, Cancel (manager sends for admin review)
                with ui.row().classes("gap-3 justify-end mt-4 w-full"):
                    complete_btn = ui.button("Complete", icon="check_circle").props("color=positive")
                    save_btn = ui.button("Save", icon="save").props("color=primary")
                    ui.button("Cancel", icon="cancel", on_click=contract_decision_dialog.close).props("flat color=grey")

                def can_complete():
                    if decision_select.value == "Renew":
                        return bool((end_date_input.value or "").strip())
                    has_existing = contract_obj and contract_obj.termination_documents and len(contract_obj.termination_documents) > 0
                    has_upload = term_doc_upload_ref.get("content")
                    return has_existing or bool(has_upload)

                def set_complete_state():
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
                            with httpx.Client(timeout=30.0) as client:
                                payload = {
                                    "contract_id": contract_db_id,
                                    "status": "pending_review",
                                    "response_provided_by_user_id": current_user_id,
                                    "initial_expiration_date": end_val.replace('/', '-') if '/' in end_val else end_val,
                                    "decision": "Extend",
                                    "decision_comments": comments_input.value or "",
                                }
                                resp = client.post("http://localhost:8000/api/v1/contract-updates", json=payload)
                                if resp.status_code not in (200, 201):
                                    ui.notify(resp.json().get("detail", "Failed to send for review"), type="negative")
                                    return
                            ui.notify("Contract sent for admin review (extend).", type="positive")
                            contract_rows[:] = get_contracts_requiring_attention()
                            contracts_table.rows = contract_rows
                            contracts_table.update()
                        except Exception as e:
                            ui.notify(f"Error sending for review: {e}", type="negative")
                            return
                    else:
                        has_upload = term_doc_upload_ref.get("content")
                        if has_upload:
                            tname = (term_doc_name_input.value or "").strip()
                            tdate = (term_doc_date_input.value or "").strip()
                            if not tname or not tdate:
                                ui.notify("Document name and Issue Date are required for the uploaded termination document.", type="negative")
                                return
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
                        try:
                            with httpx.Client(timeout=30.0) as client:
                                payload = {
                                    "contract_id": contract_db_id,
                                    "status": "pending_review",
                                    "response_provided_by_user_id": current_user_id,
                                    "has_document": bool(has_upload),
                                    "decision": "Terminate",
                                    "decision_comments": comments_input.value or "",
                                }
                                resp = client.post("http://localhost:8000/api/v1/contract-updates", json=payload)
                                if resp.status_code not in (200, 201):
                                    ui.notify(resp.json().get("detail", "Failed to send for review"), type="negative")
                                    return
                            ui.notify("Contract sent for admin review (terminate).", type="positive")
                            contract_rows[:] = get_contracts_requiring_attention()
                            contracts_table.rows = contract_rows
                            contracts_table.update()
                        except Exception as e:
                            ui.notify(f"Error sending for review: {e}", type="negative")
                            return
                    contract_decision_dialog.close()

                def do_save():
                    """Save progress without submitting for review."""
                    try:
                        from app.db.database import SessionLocal
                        from app.models.contract import ContractUpdate, ContractUpdateStatus
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
                            comments = comments_input.value or ""
                            if decision_select.value == "Terminate":
                                tname = (term_doc_name_input.value or "").strip()
                                tdate = (term_doc_date_input.value or "").strip()
                                if tname or tdate:
                                    comments = (comments + "\n" if comments else "") + f"[Planned termination doc: {tname or '(not set)'}, date: {tdate or '(not set)'}]"
                            upd.decision_comments = comments
                            upd.response_provided_by_user_id = current_user_id
                            if decision_select.value == "Renew":
                                end_val = (end_date_input.value or "").strip()
                                if end_val:
                                    upd.initial_expiration_date = datetime.strptime(end_val.replace("/", "-"), "%Y-%m-%d").date()
                            upd.has_document = bool(term_doc_upload_ref.get("content") or (contract_obj and contract_obj.termination_documents))
                            upd.updated_at = datetime.utcnow()
                            db_save.commit()
                            ui.notify("Progress saved", type="positive")
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

        def open_contract_dialog(row_data):
            selected_contract.clear()
            selected_contract["id"] = row_data.get("id")
            selected_contract["contract_id"] = row_data.get("contract_id", "")
            selected_contract["vendor_name"] = row_data.get("vendor_name", "N/A")
            selected_contract["expiration_date"] = row_data.get("expiration_date", "N/A")
            selected_contract["status"] = row_data.get("status", "Requiring attention")
            selected_contract["decision"] = row_data.get("decision")
            populate_dialog_content()
            contract_decision_dialog.open()
        
