
from datetime import datetime, timedelta

import requests
from nicegui import ui


def home_page():
    # Global variables for table and data
    contracts_table = None
    contract_rows = []
    manager_label = None
    
    # Fetch vendor count from database
    vendor_count = 0
    try:
        from app.db.database import SessionLocal
        from app.services.vendor_service import VendorService
        db = SessionLocal()
        try:
            vendor_service = VendorService(db)
            _, vendor_count = vendor_service.get_vendors_with_filters(skip=0, limit=1, status_filter=None, search=None)
        finally:
            db.close()
    except Exception as e:
        print(f"Error fetching vendor count: {e}")
        vendor_count = 0
    
    # Fetch active contracts count from database
    active_contracts_count = 0
    try:
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
    
    # Function to show the contracts table
    def show_contracts_table():
        contracts_table_container.visible = True
        # recent_activity_container.visible = False  # Commented out - Recent Activity is hidden
    
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
    
    # Quick Stats Cards (shrink to table width)
    with ui.element("div").classes("max-w-6xl mx-auto w-full"):
        with ui.row().classes(
            "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 mt-8 gap-6 w-full"
        ):
            # Row 1
            with ui.link(target='/active-contracts').classes('no-underline w-full').style('text-decoration: none !important;'):
                with ui.card().classes("w-full cursor-pointer hover:bg-gray-50 transition-colors shadow-lg").props('flat'):
                    with ui.row().classes('items-center gap-2'):
                        ui.icon('article', color='primary').style('font-size: 28px')
                ui.label("Active Contracts").classes("text-lg font-bold")
                ui.label("Currently active contracts").classes("text-sm text-gray-500")
                ui.label(str(active_contracts_count)).classes("text-2xl font-medium text-primary mt-2")
            with ui.link(target='/pending-contracts').classes('no-underline w-full').style('text-decoration: none !important;'):
                with ui.card().classes("w-full cursor-pointer hover:bg-gray-50 transition-colors shadow-lg").props('flat'):
                    with ui.row().classes('items-center gap-2'):
                        ui.icon('edit', color='primary').style('font-size: 28px')
                ui.label("Pending Documents").classes("text-lg font-bold")
                ui.label("Contracts missing documents").classes("text-sm text-gray-500")
                ui.label("12").classes("text-2xl font-medium text-primary mt-2")
            with ui.link(target='/contract-managers').classes('no-underline w-full').style('text-decoration: none !important;'):
                with ui.card().classes("w-full cursor-pointer hover:bg-gray-50 transition-colors shadow-lg").props('flat'):
                    with ui.row().classes('items-center gap-2'):
                        ui.icon('people', color='primary').style('font-size: 28px')
                ui.label("List Contract Managers").classes("text-lg font-bold")
                ui.label("Owners & Backups").classes("text-sm text-gray-500")
                ui.label("15").classes("text-2xl font-medium text-primary mt-2")
            
            # Row 2
            with ui.link(target='/pending-reviews').classes('no-underline w-full').style('text-decoration: none !important;'):
                with ui.card().classes("w-full cursor-pointer hover:bg-gray-50 transition-colors shadow-lg").props('flat'):
                    with ui.row().classes('items-center gap-2'):
                        ui.icon('pending', color='primary').style('font-size: 28px')
                ui.label("Pending Reviews").classes("text-lg font-bold")
                ui.label("Contracts awaiting review").classes("text-sm text-gray-500")
                ui.label("23").classes("text-2xl font-medium text-primary mt-2")
            with ui.link(target='/vendors').classes('no-underline w-full').style('text-decoration: none !important;'):
                with ui.card().classes("w-full cursor-pointer hover:bg-gray-50 transition-colors shadow-lg").props('flat'):
                    with ui.row().classes('items-center gap-2'):
                        ui.icon('business', color='primary').style('font-size: 28px')
                ui.label("Vendors List").classes("text-lg font-bold")
                ui.label("View all registered vendors").classes("text-sm text-gray-500")
                ui.label(str(vendor_count)).classes("text-2xl font-medium text-primary mt-2")
            with ui.card().classes("w-full cursor-pointer hover:bg-gray-50 transition-colors shadow-lg").props('flat').on('click', show_contracts_table):
                with ui.row().classes('items-center gap-2'):
                    ui.icon('warning', color='primary').style('font-size: 28px')
                ui.label("Contracts Requiring Attention").classes("text-lg font-bold")
                ui.label("Contracts approaching or past their expiration date").classes("text-sm text-gray-500")
                ui.label("8").classes("text-2xl font-medium text-primary mt-2")
            with ui.link(target='/contract-updates').classes('no-underline w-full').style('text-decoration: none !important;'):
                with ui.card().classes("w-full cursor-pointer hover:bg-gray-50 transition-colors shadow-lg").props('flat'):
                    with ui.row().classes('items-center gap-2'):
                        ui.icon('update', color='primary').style('font-size: 28px')
                    ui.label("Contract Updates").classes("text-lg font-bold")
                    ui.label("Review manager responses and updates").classes("text-sm text-gray-500")
                    ui.label("15").classes("text-2xl font-medium text-primary mt-2")

    # ===== COMMENTED OUT: Recent Activity Section =====
    # Container for the Recent Activity section
    # recent_activity_container = ui.element("div").classes("max-w-6xl mt-8 mx-auto w-full")
    # 
    # with recent_activity_container:
    #     with ui.card().classes("mt-8 w-full"):
    #         ui.label("Recent Activity").classes("text-lg font-bold")
    #         ui.label("Latest contract management activities").classes(
    #             "text-sm text-gray-500 mb-4"
    #         )
    #         with ui.column().classes("space-y-4 w-full"):
    #             with ui.row().classes(
    #                 "flex items-center justify-between py-2 border-b border-gray-200 last:border-b-0 w-full"
    #             ):
    #                 with ui.column():
    #                     ui.label("New contract created").classes("font-medium")
    #                     ui.label("Contract #CTR-2024-001 with ABC Corp").classes(
    #                         "text-sm text-gray-500"
    #                     )
    #                 ui.label("2 hours ago").classes("text-sm text-gray-500")
    #             with ui.row().classes(
    #                 "flex items-center justify-between py-2 border-b border-gray-200 last:border-b-0 w-full"
    #             ):
    #                 with ui.column():
    #                     ui.label("Vendor registered").classes("font-medium")
    #                     ui.label("XYZ Services added to vendor database").classes(
    #                         "text-sm text-gray-500"
    #                     )
    #                 ui.label("4 hours ago").classes("text-sm text-gray-500")
    #             with ui.row().classes(
    #                 "flex items-center justify-between py-2 border-b border-gray-200 last:border-b-0 w-full"
    #             ):
    #                 with ui.column():
    #                     ui.label("Contract approved").classes("font-medium")
    #                     ui.label(
    #                         "Contract #CTR-2024-002 approved by management"
    #                     ).classes("text-sm text-gray-500")
    #                 ui.label("1 day ago").classes("text-sm text-gray-500")

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
    
    # Container for the contracts table (initially hidden)
    contracts_table_container = ui.element("div").classes("max-w-6xl mt-8 mx-auto w-full")
    contracts_table_container.visible = False
    
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
            }
            .contracts-table tbody tr:has(td:contains("past due")) {
                background-color: #fee2e2 !important;
            }
            .contracts-table tbody tr:has(td:contains("remaining")) {
                background-color: #fef3c7 !important;
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
