
from nicegui import ui
from app.db.database import SessionLocal
from app.services.vendor_service import VendorService
from app.models.vendor import VendorStatusType
from datetime import date


def vendors_list():
    # Navigation
    with ui.row().classes("max-w-6xl mx-auto mt-4 items-center gap-4"):
        with ui.link(target='/').classes('no-underline'):
            ui.button("Back to Dashboard", icon="arrow_back").props('flat color=primary')
    
    # Global variables
    vendors_table = None
    vendor_rows = []
    manager_label = None
    
    # Function to handle owned/backup toggle
    def on_role_toggle(e):
        role = e.value  # Will be 'backup' or 'owned'
        
        # Filter vendors based on selected role
        filtered = [row for row in vendor_rows if row['role'] == role]
        
        # Update manager name based on role
        if role == 'backup':
            manager_name = "John Doe"
            ui.notify("Showing backup vendors (John Doe)", type="info")
        else:  # owned
            manager_name = "William Defoe"
            ui.notify("Showing owned vendors (William Defoe)", type="info")
        
        # Update the manager label
        manager_label.set_text(f"Manager: {manager_name}")
        
        # If there's an active search, reapply it to the new filtered set
        try:
            search_term = (search_input.value or "").lower()
            if search_term:
                filtered = [
                    row for row in filtered
                    if search_term in (row.get("vendor_id") or "").lower()
                    or search_term in (row.get("vendor_name") or "").lower()
                    or search_term in (row.get("contact") or "").lower()
                    or search_term in (row.get("email") or "").lower()
                    or search_term in (row.get("manager") or "").lower()
                ]
        except NameError:
            pass  # search_input not yet defined
        
        # Update table with filtered results
        vendors_table.rows = filtered
        vendors_table.update()
    
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
            vendors, total_count = vendor_service.get_vendors_with_filters(
                skip=0,
                limit=1000,
                status_filter=None,
                search=None
            )
            
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
        
        # Manager name and description row
        with ui.row().classes('items-center justify-between ml-4 mb-4 w-full'):
            ui.label("List of all vendors").classes("text-sm text-gray-500")
            manager_label = ui.label("Manager: John Doe").classes("text-base font-semibold text-primary")
        
        # Count label row
        with ui.row().classes('ml-4 mb-2'):
            count_label = ui.label(f"Total: {len(vendor_rows)} vendors").classes("text-sm text-gray-500")
        
        # Search functionality (defined before table so it can reference vendors_table)
        def filter_vendors():
            if not vendors_table:
                return
            
            # Get base rows based on current toggle state
            current_role = role_toggle.value
            base_rows = [row for row in vendor_rows if row['role'] == current_role]
            
            search_term = (search_input.value or "").lower()
            if not search_term:
                vendors_table.rows = base_rows
            else:
                filtered = [
                    row for row in base_rows
                    if search_term in (row.get("vendor_id") or "").lower()
                    or search_term in (row.get("vendor_name") or "").lower()
                    or search_term in (row.get("contact") or "").lower()
                    or search_term in (row.get("email") or "").lower()
                    or search_term in (row.get("manager") or "").lower()
                ]
                vendors_table.rows = filtered
            vendors_table.update()
        
        def clear_search():
            search_input.value = ""
            filter_vendors()
        
        # Search input
        with ui.row().classes('w-full ml-4 mr-4 mb-6 gap-2 px-2'):
            search_input = ui.input(placeholder='Search by Vendor ID, Name, Contact, or Email...').classes(
                'flex-1'
            ).props('outlined dense clearable')
            with search_input.add_slot('prepend'):
                ui.icon('search').classes('text-gray-400')
            ui.button(icon='search', on_click=filter_vendors).props('color=primary')
            ui.button(icon='clear', on_click=clear_search).props('color=secondary')
        
        # Show message if no data
        if not vendor_rows:
            with ui.card().classes("w-full p-6"):
                ui.label("No vendors found").classes("text-lg font-bold text-gray-500")
                ui.label("Please check that the backend API is running and has vendor data.").classes("text-sm text-gray-400 mt-2")
        
        # Create table after search bar (showing backup vendors by default - John Doe)
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
        
        # Force update if we have data
        if initial_rows:
            vendors_table.update()
        
        # Refresh function (defined after table is created)
        def refresh_vendors():
            nonlocal vendor_rows
            vendor_rows = fetch_vendors()
            count_label.set_text(f"Total: {len(vendor_rows)} vendors")
            # Reapply current filters
            filter_vendors()
            ui.notify(f"Refreshed: {len(vendor_rows)} vendors loaded", type="info")
        
        # Add refresh button to header
        refresh_btn = ui.button("Refresh", icon="refresh", on_click=refresh_vendors).props('color=primary flat').classes('ml-4')
        
        search_input.on_value_change(filter_vendors)
        
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
        
        # Add slot for status column with color coding
        vendors_table.add_slot('body-cell-status', '''
            <q-td :props="props">
                <div v-if="props.row.status_color === 'green'" class="text-green-700 font-semibold">
                    {{ props.value }}
                </div>
                <div v-else class="text-gray-700 font-semibold">
                    {{ props.value }}
                </div>
            </q-td>
        ''')
        

