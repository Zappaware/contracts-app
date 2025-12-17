
from nicegui import ui
from app.db.database import SessionLocal
from app.services.vendor_service import VendorService
from app.models.vendor import VendorStatusType
from app.models.contract import ContractType, DepartmentType
from sqlalchemy.orm import joinedload
from datetime import date


def vendors_list():
    # Navigation
    with ui.row().classes("max-w-6xl mx-auto mt-4 items-center gap-4"):
        with ui.link(target='/').classes('no-underline'):
            ui.button("Back to Dashboard", icon="arrow_back").props('flat color=primary')
    
    # Global variables
    vendors_table = None
    vendor_rows = []
    filtered_rows = []  # For storing filtered results
    status_filter = None  # None = All, 'active' = Active, 'inactive' = Inactive
    
    # Function to handle owned/backup toggle
    def on_role_toggle(e):
        role = e.value  # Will be 'backup' or 'owned'
        
        # Update notification based on role
        if role == 'backup':
            ui.notify("Showing backup vendors (John Doe)", type="info")
        else:  # owned
            ui.notify("Showing owned vendors (William Defoe)", type="info")
        
        # Reapply filters (which will handle role filtering)
        try:
            apply_filters()
        except NameError:
            pass  # apply_filters not yet defined
    
    # Fetch vendors directly from database service
    def fetch_vendors():
        """
        Fetches vendors directly from the database service.
        This avoids HTTP requests and circular dependencies.
        """
        db = SessionLocal()
        try:
            vendor_service = VendorService(db)
            
            # Get all vendors (limit 1000 for display)
            # status_filter is applied at the service level
            vendors, total_count = vendor_service.get_vendors_with_filters(
                skip=0,
                limit=1000,
                status_filter=status_filter,
                search=None
            )
            
            # Load contracts for each vendor to get contract types, departments, and owners
            from app.models.contract import Contract
            from app.models.vendor import Vendor
            vendors_with_contracts = db.query(Vendor).options(
                joinedload(Vendor.contracts).joinedload(Contract.contract_owner)
            ).filter(Vendor.id.in_([v.id for v in vendors])).all()
            
            # Create a mapping of vendor_id to vendor with contracts
            vendors_dict = {v.id: v for v in vendors_with_contracts}
            
            print(f"Found {len(vendors)} vendors from database")
            
            if not vendors:
                print("No vendors found in database")
                return []
            
            # Map vendor data to table row format
            rows = []
            for vendor in vendors:
                # Format next_required_due_diligence_date
                next_dd_date = vendor.next_required_due_diligence_date
                if next_dd_date:
                    if isinstance(next_dd_date, date):
                        formatted_date = next_dd_date.strftime("%Y-%m-%d")
                    else:
                        formatted_date = str(next_dd_date)
                else:
                    formatted_date = "N/A"
                
                # Determine if due diligence is overdue
                is_overdue = False
                if vendor.next_required_due_diligence_date:
                    is_overdue = vendor.next_required_due_diligence_date.date() < date.today()
                
                # Get status
                status = vendor.status.value if hasattr(vendor.status, 'value') else str(vendor.status)
                # Active = green, Inactive = black (per requirements)
                status_color = "green" if vendor.status == VendorStatusType.ACTIVE else "black"
                
                # Get primary email
                primary_email = next(
                    (e.email for e in vendor.emails if e.is_primary),
                    vendor.emails[0].email if vendor.emails else None
                )
                
                # Assign manager based on vendor ID (alternating pattern)
                # Odd vendor IDs = William Defoe (owned), Even vendor IDs = John Doe (backup)
                if vendor.id % 2 == 1:
                    manager = "William Defoe"
                    role = "owned"
                else:
                    manager = "John Doe"
                    role = "backup"
                
                # Get vendor with contracts for filtering
                vendor_with_contracts = vendors_dict.get(vendor.id)
                
                # Get contract types, departments, and owners from vendor's contracts
                contract_types = set()
                departments = set()
                owners = set()
                
                if vendor_with_contracts and vendor_with_contracts.contracts:
                    for contract in vendor_with_contracts.contracts:
                        if contract.contract_type:
                            contract_type = contract.contract_type.value if hasattr(contract.contract_type, 'value') else str(contract.contract_type)
                            contract_types.add(contract_type)
                        if contract.department:
                            dept = contract.department.value if hasattr(contract.department, 'value') else str(contract.department)
                            departments.add(dept)
                        if contract.contract_owner:
                            owner_name = f"{contract.contract_owner.first_name} {contract.contract_owner.last_name}"
                            owners.add(owner_name)
                
                row_data = {
                    "id": int(vendor.id),  # Must be integer for row_key
                    "vendor_id": str(vendor.vendor_id or ""),
                    "vendor_name": str(vendor.vendor_name or ""),
                    "contact": str(vendor.vendor_contact_person or ""),
                    "email": str(primary_email or ""),
                    "next_dd_date": str(formatted_date),
                    "status": str(status or "Unknown"),
                    "status_color": str(status_color or "gray"),
                    "manager": str(manager),
                    "role": str(role),
                    "is_overdue": bool(is_overdue),
                    "contract_types": list(contract_types),  # List of contract types this vendor has
                    "departments": list(departments),  # List of departments this vendor has contracts in
                    "owners": list(owners),  # List of contract owners for this vendor
                }
                rows.append(row_data)
            
            print(f"Processed {len(rows)} vendor rows")
            return rows
            
        except Exception as e:
            error_msg = f"Error fetching vendors: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            ui.notify(error_msg, type="negative")
            return []
        finally:
            db.close()
    
    # Define table columns
    vendor_columns = [
        {
            "name": "vendor_id",
            "label": "Vendor ID",
            "field": "vendor_id",
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
            "name": "contact",
            "label": "Contact Person",
            "field": "contact",
            "align": "left",
            "sortable": True,
        },
        {
            "name": "email",
            "label": "Email",
            "field": "email",
            "align": "left",
            "sortable": True,
        },
        {
            "name": "next_dd_date",
            "label": "Next Due Diligence Date",
            "field": "next_dd_date",
            "align": "left",
            "sortable": True,
        },
        {
            "name": "status",
            "label": "Status",
            "field": "status",
            "align": "left",
            "sortable": True,
        },
        {
            "name": "manager",
            "label": "Manager",
            "field": "manager",
            "align": "left",
            "sortable": True,
        },
    ]
    
    vendor_columns_defaults = {
        "align": "left",
        "headerClasses": "bg-[#144c8e] text-white",
    }
    
    # Fetch vendors data - use global to allow refresh
    vendor_rows = []
    
    # Initial fetch
    vendor_rows = fetch_vendors()
    
    # Debug: Check if we have data
    print(f"Total vendor rows fetched: {len(vendor_rows)}")
    if vendor_rows:
        print(f"First row sample: {vendor_rows[0]}")
    else:
        ui.notify("No vendor data available. Please check the API connection.", type="warning")
    
    # Page header
    with ui.element("div").classes("max-w-6xl mx-auto mt-8 w-full"):
        # Section header with toggle
        with ui.row().classes('items-center justify-between ml-4 mb-4 w-full'):
            with ui.row().classes('items-center gap-2'):
                ui.icon('business', color='primary').style('font-size: 32px')
                ui.label("Vendor List").classes("text-h5 font-bold")
            
            # Toggle for Owned/Backup
            role_toggle = ui.toggle(
                {'backup': 'Backup', 'owned': 'Owned'}, 
                value='backup', 
                on_change=on_role_toggle
            ).props('toggle-color=primary text-color=primary').classes('role-toggle')
        
        # Description row
        with ui.row().classes('ml-4 mb-4 w-full'):
            ui.label("List of all vendors").classes("text-sm text-gray-500")
        
        # Count label row (will be updated by filter_vendors function)
        with ui.row().classes('ml-4 mb-2'):
            count_label = ui.label(f"Total: {len(vendor_rows)} vendor(s)").classes("text-sm text-gray-500")
        
        # Keep filter_vendors for role toggle compatibility
        def filter_vendors():
            """Legacy function for role toggle - now calls apply_filters"""
            apply_filters()
        
        # Filters and search UI (similar to vendor_contracts.py)
        with ui.card().classes("w-full mb-4 p-4"):
            ui.label("Filters & Search").classes("text-lg font-bold mb-3")
            
            # Search input
            with ui.row().classes('w-full mb-4 gap-2'):
                search_input = ui.input(
                    placeholder='Search by Vendor ID, Name, Contact, Email, or Manager...'
                ).classes('flex-1').props('outlined dense clearable')
                with search_input.add_slot('prepend'):
                    ui.icon('search').classes('text-gray-400')
            
            # Filter row
            with ui.row().classes('w-full gap-4 flex-wrap'):
                # Status filter
                status_options = ["All Statuses", "Active", "Inactive"]
                status_filter_select = ui.select(
                    options=status_options,
                    value="All Statuses",
                    label="Status"
                ).classes('flex-1 min-w-[150px]').props('outlined dense')
                
                # Type filter (Contract Type)
                type_options = ["All Types"] + [ct.value for ct in ContractType]
                type_filter = ui.select(
                    options=type_options,
                    value="All Types",
                    label="Type"
                ).classes('flex-1 min-w-[150px]').props('outlined dense')
                
                # Department filter
                dept_options = ["All Departments"] + [dept.value for dept in DepartmentType]
                department_filter = ui.select(
                    options=dept_options,
                    value="All Departments",
                    label="Department"
                ).classes('flex-1 min-w-[150px]').props('outlined dense')
                
                # Owner filter (get unique owners from vendor contracts)
                unique_owners = set()
                for row in vendor_rows:
                    unique_owners.update(row.get("owners", []))
                unique_owners = sorted([owner for owner in unique_owners if owner])
                owner_options = ["All Owners"] + unique_owners
                owner_filter = ui.select(
                    options=owner_options,
                    value="All Owners",
                    label="Owner"
                ).classes('flex-1 min-w-[150px]').props('outlined dense')
            
            # Action buttons
            with ui.row().classes('w-full gap-2 mt-2'):
                filter_btn = ui.button("Apply Filters", icon="filter_list").props('color=primary')
                clear_btn = ui.button("Clear Filters", icon="clear").props('color=secondary')
        
        # Filter and search function
        def apply_filters():
            nonlocal filtered_rows, status_filter, vendor_rows
            if not vendors_table:
                return
            
            # Sync status_filter with status_filter_select for fetch_vendors compatibility
            # Convert "All Statuses" to None, "Active" to 'active', "Inactive" to 'inactive'
            if status_filter_select.value == "All Statuses":
                status_filter = None
            elif status_filter_select.value == "Active":
                status_filter = 'active'
            elif status_filter_select.value == "Inactive":
                status_filter = 'inactive'
            else:
                status_filter = status_filter_select.value
            
            # Get base rows based on current toggle state
            current_role = role_toggle.value
            filtered_rows = [row for row in vendor_rows if row['role'] == current_role]
            
            # Apply status filter (double-check at display level)
            if status_filter_select.value and status_filter_select.value != "All Statuses":
                status_value = status_filter_select.value
                if status_value == 'Active':
                    filtered_rows = [r for r in filtered_rows if r.get('status', '').lower() == 'active']
                elif status_value == 'Inactive':
                    filtered_rows = [r for r in filtered_rows if r.get('status', '').lower() == 'inactive']
            
            # Apply type filter (Contract Type)
            if type_filter.value and type_filter.value != "All Types":
                filtered_rows = [r for r in filtered_rows if type_filter.value in r.get('contract_types', [])]
            
            # Apply department filter
            if department_filter.value and department_filter.value != "All Departments":
                filtered_rows = [r for r in filtered_rows if department_filter.value in r.get('departments', [])]
            
            # Apply owner filter
            if owner_filter.value and owner_filter.value != "All Owners":
                filtered_rows = [r for r in filtered_rows if owner_filter.value in r.get('owners', [])]
            
            # Apply search
            search_term = (search_input.value or "").lower()
            if search_term:
                filtered_rows = [
                    r for r in filtered_rows
                    if search_term in (r.get("vendor_id") or "").lower()
                    or search_term in (r.get("vendor_name") or "").lower()
                    or search_term in (r.get("contact") or "").lower()
                    or search_term in (r.get("email") or "").lower()
                    or search_term in (r.get("manager") or "").lower()
                ]
            
            # Update table with filtered results
            vendors_table.rows = filtered_rows
            vendors_table.update()
            
            # Show/hide "No results found" message
            if len(filtered_rows) == 0:
                no_results_msg.visible = True
            else:
                no_results_msg.visible = False
            
            # Update count label
            count_label.set_text(f"Showing: {len(filtered_rows)} of {len(vendor_rows)} vendor(s)")
        
        def clear_filters():
            """Clear both search and all filters"""
            nonlocal status_filter, vendor_rows
            search_input.value = ""
            status_filter_select.value = "All Statuses"
            type_filter.value = "All Types"
            department_filter.value = "All Departments"
            owner_filter.value = "All Owners"
            status_filter = None
            
            # Refresh vendors without filters
            vendor_rows = fetch_vendors()
            apply_filters()  # This will update count and show/hide no results message
            ui.notify("All filters and search cleared", type="info")
        
        # Bind filter events
        filter_btn.on_click(apply_filters)
        clear_btn.on_click(clear_filters)
        search_input.on_value_change(apply_filters)
        
        # Show message if no data at all
        if not vendor_rows:
            with ui.card().classes("w-full p-6"):
                ui.label("No vendors found").classes("text-lg font-bold text-gray-500")
                ui.label("Please check that the backend API is running and has vendor data.").classes("text-sm text-gray-400 mt-2")
        
        # "No results found" message (initially hidden, shown when filters/search return no results)
        with ui.card().classes("w-full p-6") as no_results_msg:
            no_results_msg.visible = False
            ui.label("No results found").classes("text-lg font-bold text-gray-500")
            ui.label("Try adjusting your search or filters.").classes("text-sm text-gray-400 mt-2")
            with ui.row().classes("gap-2 mt-4"):
                ui.button("Clear All Filters", icon="clear", on_click=clear_filters).props('color=orange')
        
        # Create table after search bar (showing backup vendors by default - John Doe)
        # Apply role filter only (status and search filters will be applied via apply_filters)
        initial_rows = [row for row in vendor_rows if row.get('role') == 'backup']
        print(f"Creating table with {len(initial_rows)} rows (filtered by role: backup)")
        
        vendors_table = ui.table(
            columns=vendor_columns,
            column_defaults=vendor_columns_defaults,
            rows=initial_rows,
            pagination=10,
            row_key="id"
        ).classes("w-full").props("flat bordered").classes(
            "vendors-table shadow-lg rounded-lg overflow-hidden"
        )
        
        # Update count label and check for no results initially
        if len(initial_rows) == 0:
            no_results_msg.visible = True
            count_label.set_text(f"Showing: 0 of {len(vendor_rows)} vendor(s)")
        else:
            no_results_msg.visible = False
            count_label.set_text(f"Showing: {len(initial_rows)} of {len(vendor_rows)} vendor(s)")
        
        # Force update if we have data
        if initial_rows:
            vendors_table.update()
        
        # Apply initial filters
        apply_filters()
        
        # Refresh function (defined after table is created)
        def refresh_vendors():
            nonlocal vendor_rows
            vendor_rows = fetch_vendors()
            # Reapply current filters
            apply_filters()
            ui.notify(f"Refreshed: {len(vendor_rows)} vendors loaded", type="info")
        
        # Add refresh button to header
        refresh_btn = ui.button("Refresh", icon="refresh", on_click=refresh_vendors).props('color=primary flat').classes('ml-4')
        
        # Add custom CSS
        ui.add_css("""
            .vendors-table thead tr {
                background-color: #144c8e !important;
            }
            .vendors-table tbody tr {
                background-color: white !important;
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
        vendors_table.add_slot('body-cell-vendor_name', '''
            <q-td :props="props">
                <a :href="'/vendor-info/' + props.row.id" class="text-blue-600 hover:text-blue-800 underline cursor-pointer">
                    {{ props.value }}
                </a>
            </q-td>
        ''')
        
        # Add slot for status column with color coding (Active=green, Inactive=black per requirements)
        vendors_table.add_slot('body-cell-status', '''
            <q-td :props="props">
                <div v-if="props.row.status_color === 'green'" class="text-green-700 font-semibold">
                    {{ props.value }}
                </div>
                <div v-else class="text-black font-semibold">
                    {{ props.value }}
                </div>
            </q-td>
        ''')
        

