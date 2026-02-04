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
    with ui.column().classes("max-w-6xl mx-auto w-full gap-0"):
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

        # ===== Contracts Requiring Attention table (same as admin – visible on manager load) =====
    # with ui.element("div").classes("max-w-6xl mt-8 mx-auto w-full"):
    #     ui.label("Vendor List").classes("text-h5 ml-4 font-bold ")
    #
    # columns = [
    #     {
    #         "name": "id",
    #         "label": "Id",
    #         "field": "id",
    #         "align": "left",
    #     },
    #     {
    #         "name": "name",
    #         "label": "Name",
    #         "field": "name",
    #         "align": "left",
    #     },
    #     {
    #         "name": "contact",
    #         "label": "Contact Person",
    #         "field": "contact",
    #         "align": "left",
    #     },
    #     {
    #         "name": "country",
    #         "label": "Country",
    #         "field": "country",
    #         "align": "left",
    #     },
    #     {
    #         "name": "telephone",
    #         "label": "Telephone",
    #         "field": "telephone",
    #         "align": "left",
    #     },
    #     {
    #         "name": "email",
    #         "label": "Email",
    #         "field": "email",
    #         "align": "left",
    #     },
    #     {
    #         "name": "D.D. Performed",
    #         "label": "D.D. Performed",
    #         "field": "dd_performed",
    #         "align": "left",
    #     },
    #     {
    #         "name": "attention",
    #         "label": "Attention",
    #         "field": "attention",
    #         "align": "left",
    #     },
    # ]
    # columns_defaults = {
    #     "align": "left",
    #     "headerClasses": "bg-[#144c8e] text-white",
    # }
    # def fetch_vendors():
    #     url = "http://localhost:8000/api/v1/vendors/"
    #     try:
    #         response = requests.get(url)
    #         response.raise_for_status()
    #         vendor_list = response.json()
    #         # Map backend vendor data to table row format
    #         rows = []
    #         for v in vendor_list:
    #             rows.append({
    #                 "id": v.get("id", ""),
    #                 "name": v.get("vendor_name", ""),
    #                 "contact": v.get("vendor_contact_person", ""),
    #                 "country": v.get("vendor_country", ""),
    #                 "telephone": v.get("phones", [{}])[0].get("phone_number", "") if v.get("phones") else "",
    #                 "email": v.get("emails", [{}])[0].get("email", "") if v.get("emails") else "",
    #                 "dd_performed": "Yes" if v.get("due_diligence_required", "No") == "Yes" else "No",
    #                 "attention": v.get("attention", "")
    #             })
    #         return rows
    #     except Exception as e:
    #         ui.notify(f"Error fetching vendors: {e}", type="negative")
    #         return []
    #
    # rows = fetch_vendors()
    #
    # with ui.element("div").classes("max-w-6xl mx-auto w-full"):
    #     ui.table(
    #         columns=columns, column_defaults=columns_defaults, rows=rows, pagination=3
    #     ).classes("w-full").props("flat").classes(
    #         "vendor-table shadow-lg rounded-lg overflow-hidden"
    #     )
    #     ui.add_css(".vendor-table thead tr { background-color: #144c8e !important; }")

    
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
            from app.models.contract import ContractStatusType, Contract, ExpirationNoticePeriodType
            from sqlalchemy import or_, and_
            from sqlalchemy.orm import joinedload
            
            db = SessionLocal()
            try:
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
                
                # Filter contracts that have reached notification window
                contracts_in_window = []
                for contract in contracts:
                    if not contract.end_date:
                        continue
                    
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
    
    # Table section: same as admin "Contracts Requiring Attention" table, visible when manager page loads
    with ui.element("div").classes("mt-8 w-full"):
        # Section header - same as admin mode "Contracts Requiring Attention" table
        with ui.row().classes('items-center justify-between ml-4 mb-4 w-full'):
            with ui.row().classes('items-center gap-2'):
                ui.icon('warning', color='orange').style('font-size: 32px')
                ui.label("Contracts Requiring Attention").classes("text-h5 font-bold")
        
        # Description row - same as admin mode
        with ui.row().classes('ml-4 mb-4 w-full'):
            ui.label("Contracts approaching or past their expiration date").classes(
                "text-sm text-gray-500"
            )
        
        # Role filter dropdown
        role_filter = None
        with ui.row().classes('w-full ml-4 mr-4 mb-4 gap-4 px-2'):
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
        
        # Search input for filtering contracts (above the table) - same as admin mode
        with ui.row().classes('w-full ml-4 mr-4 mb-6 gap-2 px-2'):
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
        
        # Create table after search bar
        initial_rows = contract_rows if contract_rows else []
        contracts_table = ui.table(
            columns=contract_columns,
            column_defaults=contract_columns_defaults,
            rows=initial_rows,
            pagination=10,
            row_key="contract_id"
        ).classes("w-full").props("flat bordered").classes(
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
        
        # Add slot for custom styling of status column
        contracts_table.add_slot('body-cell-status', '''
            <q-td :props="props">
                <div v-if="props.value.includes('Termination Pending')" class="text-orange-700 font-bold flex items-center gap-1">
                    <q-icon name="pending" color="orange" size="sm" />
                    {{ props.value }}
                </div>
                <div v-else-if="props.value.includes('past due')" class="text-red-700 font-bold flex items-center gap-1">
                    <q-icon name="error" color="red" size="sm" />
                    {{ props.value }}
                </div>
                <div v-else class="text-orange-600 font-semibold flex items-center gap-1">
                    <q-icon name="warning" color="orange" size="sm" />
                    {{ props.value }}
                </div>
            </q-td>
        ''')
        
        # Store contract data for dialog access
        stored_contract_data = {}
        
        # Extend/Terminate Dialog
        with ui.dialog() as extend_terminate_dialog, ui.card().classes("min-w-[600px] max-w-3xl"):
            ui.label("Contract Decision").classes("text-h5 mb-4 text-blue-600")
            
            # Contract details display
            contract_details_display = ui.element("div").classes("mb-4 p-4 bg-gray-50 rounded-lg w-full")
            
            # Decision selection
            with ui.column().classes("space-y-4 w-full"):
                ui.label("Select Decision").classes("text-lg font-bold")
                
                decision_radio = ui.radio(['Extend', 'Terminate'], value='Extend').props('inline color=primary')
                
                # Extend section (initially visible)
                extend_section = ui.element("div").classes("w-full mt-4")
                with extend_section:
                    ui.label("New Expiration Date*").classes("font-medium mb-2")
                    new_expiration_date = ui.input('MM/DD/YYYY', placeholder='Select new expiration date*').classes("w-full").props("outlined")
                    new_expiration_date_menu = None
                    with new_expiration_date:
                        with ui.menu().props('no-parent-event') as new_expiration_date_menu:
                            with ui.date().props('mask=MM/DD/YYYY').bind_value(new_expiration_date, 
                                forward=lambda d: d.replace('-', '/') if d else '', 
                                backward=lambda d: d.replace('/', '-') if d else ''):
                                with ui.row().classes('justify-end'):
                                    ui.button('Close', on_click=new_expiration_date_menu.close).props('flat')
                        with new_expiration_date.add_slot('append'):
                            ui.icon('edit_calendar').on('click', new_expiration_date_menu.open).classes('cursor-pointer')
                    extend_date_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
                
                # Terminate section (initially hidden)
                terminate_section = ui.element("div").classes("w-full mt-4 hidden")
                with terminate_section:
                    ui.label("Termination Document (PDF)").classes("font-medium mb-2")
                    termination_uploaded_files = []
                    
                    def handle_termination_upload(e):
                        if e.file_names:
                            for file_name in e.file_names:
                                if file_name.lower().endswith('.pdf'):
                                    termination_uploaded_files.append(file_name)
                                    ui.notify(f'Uploaded {file_name}', type='positive')
                                else:
                                    ui.notify('Only PDF files are allowed', type='negative')
                    
                    ui.upload(
                        on_upload=handle_termination_upload,
                        label="Drop PDF file here or click to browse (Optional)"
                    ).props('accept=.pdf color=primary outlined').classes("w-full")
                
                # Action buttons
                with ui.row().classes("gap-4 mt-6 justify-end"):
                    process_btn = ui.button("Process", icon="check_circle").props('color=primary')
                    cancel_dialog_btn = ui.button("Cancel", icon="cancel").props('color=grey')
            
            # Status indicator
            dialog_status_indicator = ui.element("div").classes("mt-4 p-4 rounded-lg hidden")
            
            # Function to toggle between Extend and Terminate sections
            def on_decision_change(e):
                if decision_radio.value == 'Extend':
                    extend_section.classes(remove='hidden')
                    terminate_section.classes(add='hidden')
                else:
                    extend_section.classes(add='hidden')
                    terminate_section.classes(remove='hidden')
            
            decision_radio.on('change', on_decision_change)
            
            # Validation function
            def validate_decision():
                if decision_radio.value == 'Extend':
                    date_value = new_expiration_date.value or ''
                    if not date_value.strip():
                        extend_date_error.text = "Please select a new expiration date"
                        extend_date_error.style('display:block')
                        new_expiration_date.classes('border border-red-600')
                        return False
                    else:
                        extend_date_error.text = ''
                        extend_date_error.style('display:none')
                        new_expiration_date.classes(remove='border border-red-600')
                        return True
                else:  # Terminate
                    # Termination document is optional, so always valid
                    return True
            
            # Process function
            def process_decision():
                if not validate_decision():
                    ui.notify('Please fix validation errors', type='negative')
                    return
                
                decision = decision_radio.value
                # Get contract ID from the details display or use a stored value
                contract_id = "Unknown"
                try:
                    # Try to extract from contract_details_display
                    contract_id = stored_contract_data.get('contract_id', 'Unknown')
                except Exception:
                    pass
                
                if decision == 'Extend':
                    new_date = new_expiration_date.value
                    # Send to backend: create/update ContractUpdate as pending_review with decision + proposed end date
                    try:
                        import httpx
                        contract_db_id = stored_contract_data.get('id')
                        if not contract_db_id:
                            ui.notify('Error: missing contract database id', type='negative')
                            return
                        with httpx.Client(timeout=30.0) as client:
                            payload = {
                                "contract_id": contract_db_id,
                                "status": "pending_review",
                                "response_provided_by_user_id": current_user_id,
                                # Store the manager-provided new end date in initial_expiration_date
                                "initial_expiration_date": new_date.replace('/', '-') if '/' in new_date else new_date,
                                "decision": "Extend",
                                "decision_comments": "",
                            }
                            resp = client.post("http://localhost:8000/api/v1/contract-updates", json=payload)
                            if resp.status_code not in (200, 201):
                                ui.notify(f'Error sending update for review ({resp.status_code})', type='negative')
                                return
                        ui.notify(f'Contract {contract_id} sent for admin review (extend to {new_date})', type='positive')
                    except Exception as e:
                        ui.notify(f'Error sending update for review: {e}', type='negative')
                        return
                    dialog_status_indicator.classes(remove="hidden")
                    dialog_status_indicator.classes("bg-green-100 border border-green-400 text-green-700")
                    dialog_status_indicator.clear()
                    with dialog_status_indicator:
                        ui.icon('check_circle', color='green').classes('text-2xl')
                        ui.label("Contract Extended Successfully!").classes("ml-2 font-bold")
                        ui.label(f"New expiration date: {new_date}").classes("ml-2 text-sm")
                else:  # Terminate
                    doc_count = len(termination_uploaded_files)
                    # Update contract status in contract_rows
                    for row in contract_rows:
                        if row.get('contract_id') == contract_id:
                            row['status'] = "Termination Pending – Documents Required"
                            row['status_class'] = "termination_pending"
                            row['row_class'] = "bg-orange-50"
                            break
                    
                    # Update table
                    contracts_table.rows = contract_rows
                    contracts_table.update()
                    
                    # Send to backend: create/update ContractUpdate as pending_review with decision Terminate
                    try:
                        import httpx
                        contract_db_id = stored_contract_data.get('id')
                        if not contract_db_id:
                            ui.notify('Error: missing contract database id', type='negative')
                            return
                        with httpx.Client(timeout=30.0) as client:
                            payload = {
                                "contract_id": contract_db_id,
                                "status": "pending_review",
                                "response_provided_by_user_id": current_user_id,
                                "has_document": bool(doc_count),
                                "decision": "Terminate",
                                "decision_comments": "",
                            }
                            resp = client.post("http://localhost:8000/api/v1/contract-updates", json=payload)
                            if resp.status_code not in (200, 201):
                                ui.notify(f'Error sending termination for review ({resp.status_code})', type='negative')
                                return
                        ui.notify(f'Contract {contract_id} sent for admin review (terminate)', type='positive')
                    except Exception as e:
                        ui.notify(f'Error sending termination for review: {e}', type='negative')
                        return
                    dialog_status_indicator.classes(remove="hidden")
                    dialog_status_indicator.classes("bg-green-100 border border-green-400 text-green-700")
                    dialog_status_indicator.clear()
                    with dialog_status_indicator:
                        ui.icon('check_circle', color='green').classes('text-2xl')
                        ui.label("Termination Decision Saved!").classes("ml-2 font-bold")
                        ui.label("Status: Termination Pending – Documents Required").classes("ml-2 text-sm font-bold text-orange-600")
                        if doc_count > 0:
                            ui.label(f"Uploaded {doc_count} document(s)").classes("ml-2 text-sm")
                
                # Hide form and show status
                decision_radio.visible = False
                extend_section.visible = False
                terminate_section.visible = False
                process_btn.visible = False
                cancel_dialog_btn.visible = False
            
            def cancel_dialog():
                extend_terminate_dialog.close()
                # Reset form
                decision_radio.value = 'Extend'
                new_expiration_date.value = ''
                termination_uploaded_files.clear()
                extend_date_error.text = ''
                extend_date_error.style('display:none')
                dialog_status_indicator.classes(add='hidden')
                decision_radio.visible = True
                extend_section.visible = True
                terminate_section.visible = True
                process_btn.visible = True
                cancel_dialog_btn.visible = True
            
            process_btn.on_click(process_decision)
            cancel_dialog_btn.on_click(cancel_dialog)
        
        # Function to open dialog when contract row is clicked
        def open_contract_dialog(row_data):
            nonlocal stored_contract_data
            # Check if contract is about to expire (has "past due" or "remaining" in status)
            # Also allow opening if status is "Termination Pending" to view/update
            status = row_data.get('status', '')
            if 'past due' in status.lower() or 'remaining' in status.lower() or 'Termination Pending' in status:
                stored_contract_data = row_data
                contract_details_display.clear()
                with contract_details_display:
                    ui.label(f"Contract ID: {row_data.get('contract_id', 'N/A')}").classes("font-bold text-lg")
                    ui.label(f"Vendor: {row_data.get('vendor_name', 'N/A')}").classes("text-gray-600")
                    ui.label(f"Type: {row_data.get('contract_type', 'N/A')}").classes("text-gray-600")
                    ui.label(f"Current Expiration: {row_data.get('expiration_date', 'N/A')}").classes("text-gray-600")
                    ui.label(f"Status: {row_data.get('status', 'N/A')}").classes("text-orange-600 font-bold")
                
                extend_terminate_dialog.open()
            else:
                ui.notify('This contract is not expiring soon', type='info')
        
        # Make table rows clickable by enabling selection
        contracts_table.props('selection=single')
        
        # Function to handle when a row is selected/clicked
        last_selected = None
        
        def handle_row_selection():
            nonlocal last_selected
            try:
                # Get selected row from table
                if hasattr(contracts_table, 'selected') and contracts_table.selected:
                    selected = contracts_table.selected
                    # Handle both single selection and list
                    if isinstance(selected, list):
                        if len(selected) > 0:
                            selected = selected[0]
                        else:
                            return
                    
                    # Only open dialog if it's a different row
                    if isinstance(selected, dict) and selected.get('contract_id') != last_selected:
                        last_selected = selected.get('contract_id')
                        open_contract_dialog(selected)
            except Exception:
                pass
        
        # Monitor table selection changes
        contracts_table.on('update:selected', handle_row_selection)
        
        # Also add a click handler using JavaScript for immediate response
        ui.run_javascript('''
            setTimeout(() => {
                const table = document.querySelector('.contracts-table');
                if (table) {
                    const tbody = table.querySelector('tbody');
                    if (tbody) {
                        tbody.addEventListener('click', function(e) {
                            // Find the clicked row
                            let row = e.target.closest('tr');
                            if (row && !e.target.closest('a')) {
                                // Get contract ID from first cell
                                const firstCell = row.querySelector('td');
                                if (firstCell) {
                                    const contractId = firstCell.textContent.trim();
                                    // Trigger selection by clicking the row
                                    row.click();
                                }
                            }
                        });
                    }
                }
            }, 500);
        ''')
