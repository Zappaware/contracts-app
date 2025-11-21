
from datetime import datetime, timedelta

import requests
from nicegui import ui


def manager():
    # Global variables for table and data
    contracts_table = None
    contract_rows = []
    manager_label = None
    
    # Function to handle owned/backup toggle
    def on_role_toggle(e):
        role = e.value  # Will be 'backup' or 'owned'
        
        # Filter contracts based on selected role
        filtered = [row for row in contract_rows if row['role'] == role]
        
        # Update manager name based on role
        if role == 'backup':
            manager_name = "John Doe"
            ui.notify("Showing backup contracts (John Doe)", type="info")
        else:  # owned
            manager_name = "William Defoe"
            ui.notify("Showing owned contracts (William Defoe)", type="info")
        
        # Update the manager label
        manager_label.set_text(f"Manager: {manager_name}")
        
        # If there's an active search, reapply it to the new filtered set
        try:
            search_term = (search_input.value or "").lower()
            if search_term:
                filtered = [
                    row for row in filtered
                    if search_term in (row['contract_id'] or "").lower()
                    or search_term in (row['vendor_name'] or "").lower()
                    or search_term in (row['contract_type'] or "").lower()
                    or search_term in (row['description'] or "").lower()
                    or search_term in (row['manager'] or "").lower()
                ]
        except NameError:
            pass  # search_input not yet defined
        
        # Update table with filtered results
        contracts_table.rows = filtered
        contracts_table.update()
    
    # Quick Stats Cards - Only 3 cards as requested
    with ui.element("div").classes("max-w-6xl mx-auto w-full"):
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
                    ui.label("1,247").classes("text-2xl font-medium text-primary mt-2")
            
            # Card 2: Pending Documents
            with ui.link(target='/pending-contracts').classes('no-underline w-full').style('text-decoration: none !important;'):
                with ui.card().classes("w-full cursor-pointer hover:bg-gray-50 transition-colors shadow-lg").props('flat'):
                    with ui.row().classes('items-center gap-2'):
                        ui.icon('edit', color='primary').style('font-size: 28px')
                        ui.label("Pending Documents").classes("text-lg font-bold")
                    ui.label("Contracts missing documents").classes("text-sm text-gray-500 mt-2")
                    ui.label("12").classes("text-2xl font-medium text-primary mt-2")
            
            # Card 3: Pending Reviews
            with ui.link(target='/pending-reviews').classes('no-underline w-full').style('text-decoration: none !important;'):
                with ui.card().classes("w-full cursor-pointer hover:bg-gray-50 transition-colors shadow-lg").props('flat'):
                    with ui.row().classes('items-center gap-2'):
                        ui.icon('pending', color='primary').style('font-size: 28px')
                        ui.label("Pending Reviews").classes("text-lg font-bold")
                    ui.label("Contracts awaiting review").classes("text-sm text-gray-500 mt-2")
                    ui.label("23").classes("text-2xl font-medium text-primary mt-2")

    # ===== COMMENTED OUT: Vendor List Section =====
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
    
    # Mock data for contracts requiring attention (since API is not available yet)
    def get_mock_contracts():
        """
        Simulates contracts that have reached their notification window.
        This will be replaced with actual API call when available.
        """
        today = datetime.now()
        
        mock_contracts = [
            {
                "contract_id": "CTR-2024-001",
                "vendor_name": "Acme Corp",
                "contract_type": "Service Agreement",
                "description": "IT Support Services",
                "expiration_date": today - timedelta(days=5),  # 5 days past due
                "manager": "William Defoe",
                "role": "owned"
            },
            {
                "contract_id": "CTR-2024-012",
                "vendor_name": "Beta Technologies",
                "contract_type": "Software License",
                "description": "Enterprise Software Licensing",
                "expiration_date": today - timedelta(days=15),  # 15 days past due
                "manager": "John Doe",
                "role": "backup"
            },
            {
                "contract_id": "CTR-2024-023",
                "vendor_name": "Gamma Consulting",
                "contract_type": "Consulting",
                "description": "Business Process Optimization",
                "expiration_date": today + timedelta(days=10),  # 10 days remaining
                "manager": "William Defoe",
                "role": "owned"
            },
            {
                "contract_id": "CTR-2024-034",
                "vendor_name": "Delta Logistics",
                "contract_type": "Transportation",
                "description": "Freight and Delivery Services",
                "expiration_date": today + timedelta(days=5),  # 5 days remaining
                "manager": "John Doe",
                "role": "backup"
            },
            {
                "contract_id": "CTR-2023-089",
                "vendor_name": "Epsilon Security",
                "contract_type": "Security Services",
                "description": "Building Security and Monitoring",
                "expiration_date": today - timedelta(days=30),  # 30 days past due
                "manager": "William Defoe",
                "role": "owned"
            },
            {
                "contract_id": "CTR-2024-045",
                "vendor_name": "Zeta Solutions",
                "contract_type": "Maintenance",
                "description": "Equipment Maintenance Contract",
                "expiration_date": today + timedelta(days=20),  # 20 days remaining
                "manager": "John Doe",
                "role": "backup"
            },
            {
                "contract_id": "CTR-2024-056",
                "vendor_name": "Eta Services",
                "contract_type": "Cleaning Services",
                "description": "Office Cleaning and Janitorial",
                "expiration_date": today - timedelta(days=2),  # 2 days past due
                "manager": "William Defoe",
                "role": "owned"
            },
            {
                "contract_id": "CTR-2024-067",
                "vendor_name": "Theta Communications",
                "contract_type": "Telecommunications",
                "description": "Internet and Phone Services",
                "expiration_date": today + timedelta(days=15),  # 15 days remaining
                "manager": "John Doe",
                "role": "backup"
            },
        ]
        
        rows = []
        for contract in mock_contracts:
            exp_date = contract["expiration_date"]
            days_diff = (today - exp_date).days
            
            # Calculate status and visual indicators
            if days_diff > 0:
                # Past due - RED
                status = f"{days_diff} days past due"
                status_class = "expired"
                row_class = "bg-red-50"
            else:
                # Approaching expiration - WARNING
                status = f"{abs(days_diff)} days remaining"
                status_class = "warning"
                row_class = "bg-yellow-50"
            
            rows.append({
                "contract_id": contract["contract_id"],
                "vendor_name": contract["vendor_name"],
                "contract_type": contract["contract_type"],
                "description": contract["description"],
                "expiration_date": exp_date.strftime("%Y-%m-%d"),
                "expiration_timestamp": exp_date.timestamp(),  # For sorting
                "status": status,
                "status_class": status_class,
                "row_class": row_class,
                "manager": contract["manager"],
                "role": contract["role"],
            })
        
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
    ]

    contract_columns_defaults = {
        "align": "left",
        "headerClasses": "bg-[#144c8e] text-white",
    }

    contract_rows = get_mock_contracts()
    
    # Container for the contracts table (visible by default)
    contracts_table_container = ui.element("div").classes("max-w-6xl mt-8 mx-auto w-full")
    contracts_table_container.visible = True
    
    with contracts_table_container:
        # Section header with toggle
        with ui.row().classes('items-center justify-between ml-4 mb-4 w-full'):
            with ui.row().classes('items-center gap-2'):
                ui.icon('warning', color='orange').style('font-size: 32px')
                ui.label("Contracts Requiring Attention").classes("text-h5 font-bold")
            
            # Toggle for Owned/Backup
            role_toggle = ui.toggle(
                {'backup': 'Backup', 'owned': 'Owned'}, 
                value='backup', 
                on_change=on_role_toggle
            ).props('toggle-color=primary text-color=primary').classes('role-toggle')
        
        # Manager name and description row
        with ui.row().classes('items-center justify-between ml-4 mb-4 w-full'):
            ui.label("Contracts approaching or past their expiration date").classes(
                "text-sm text-gray-500"
            )
            manager_label = ui.label("Manager: John Doe").classes(
                "text-base font-semibold text-primary"
            )
        
        # Define search functions first
        def filter_contracts():
            # Get base rows based on current toggle state
            current_role = role_toggle.value
            base_rows = [row for row in contract_rows if row['role'] == current_role]
            
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
                    or search_term in (row['manager'] or "").lower()
                ]
                contracts_table.rows = filtered
            contracts_table.update()
        
        def clear_search():
            search_input.value = ""
            filter_contracts()  # Use filter_contracts to respect current role
        
        # Search input for filtering contracts (above the table)
        with ui.row().classes('w-full ml-4 mr-4 mb-6 gap-2 px-2'):
            search_input = ui.input(placeholder='Search by Contract ID, Vendor, Type, Description, or Manager...').classes(
                'flex-1'
            ).props('outlined dense clearable')
            with search_input.add_slot('prepend'):
                ui.icon('search').classes('text-gray-400')
            ui.button(icon='search', on_click=filter_contracts).props('color=primary')
            ui.button(icon='clear', on_click=clear_search).props('color=secondary')
        
        # Create table after search bar (showing backup contracts by default - John Doe)
        initial_rows = [row for row in contract_rows if row['role'] == 'backup']
        contracts_table = ui.table(
            columns=contract_columns,
            column_defaults=contract_columns_defaults,
            rows=initial_rows,
            pagination=10,
            row_key="contract_id"
        ).classes("w-full").props("flat bordered").classes(
            "contracts-table shadow-lg rounded-lg overflow-hidden"
        )
        
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
            
            /* Toggle button styling - white background for selected button */
            .role-toggle .q-btn--active {
                background-color: white !important;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
            }
            .role-toggle .q-btn {
                font-weight: 500;
                padding: 6px 16px;
            }
        """)
        
        # Add slot for vendor name with clickable link
        contracts_table.add_slot('body-cell-vendor_name', '''
            <q-td :props="props">
                <a :href="'/vendor-info'" class="text-blue-600 hover:text-blue-800 underline cursor-pointer">
                    {{ props.value }}
                </a>
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
                    # Here you would send this to your backend/API
                    ui.notify(f'Contract {contract_id} extended to {new_date}', type='positive')
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
                    
                    # Update table if the current row is visible
                    current_role = role_toggle.value
                    filtered_rows = [row for row in contract_rows if row['role'] == current_role]
                    contracts_table.rows = filtered_rows
                    contracts_table.update()
                    
                    # Here you would send this to your backend/API
                    ui.notify(f'Contract {contract_id} marked for termination', type='positive')
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
