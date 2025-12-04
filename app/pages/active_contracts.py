from datetime import datetime, timedelta, date
from nicegui import ui
from app.db.database import SessionLocal
from app.services.contract_service import ContractService
from app.models.contract import ContractStatusType


def active_contracts():
    # Navigation
    with ui.row().classes("max-w-6xl mx-auto mt-4"):
        with ui.link(target='/').classes('no-underline'):
            ui.button("Back to Dashboard", icon="arrow_back").props('flat color=primary')
    
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
    
    # Fetch active contracts from database
    def fetch_active_contracts():
        """
        Fetches active contracts directly from the database service.
        This avoids HTTP requests and circular dependencies.
        """
        db = SessionLocal()
        try:
            contract_service = ContractService(db)
            
            # Get active contracts only (limit 1000 for display)
            contracts, _ = contract_service.search_and_filter_contracts(
                skip=0,
                limit=1000,
                status=ContractStatusType.ACTIVE,
                search=None,
                contract_type=None,
                department=None,
                owner_id=None,
                vendor_id=None,
                expiring_soon=None
            )
            
            print(f"Found {len(contracts)} active contracts from database")
            
            if not contracts:
                print("No active contracts found in database")
                return []
            
            # Map contract data to table row format
            rows = []
            for contract in contracts:
                # Get contract owner name
                owner_name = f"{contract.contract_owner.first_name} {contract.contract_owner.last_name}"
                backup_name = f"{contract.contract_owner_backup.first_name} {contract.contract_owner_backup.last_name}"
                
                # Get vendor info
                vendor_name = contract.vendor.vendor_name if contract.vendor else "Unknown"
                vendor_id = contract.vendor.id if contract.vendor else None
                
                # Get contract type value
                contract_type = contract.contract_type.value if hasattr(contract.contract_type, 'value') else str(contract.contract_type)
                
                # Get status value
                status = contract.status.value if hasattr(contract.status, 'value') else str(contract.status)
                
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
                
                # Determine role based on user (for demo, using contract owner ID)
                # Odd IDs = William Defoe (owned), Even IDs = John Doe (backup)
                # In real app, you'd check against current logged-in user
                if contract.contract_owner_id % 2 == 1:
                    manager = owner_name
                    role = "owned"
                else:
                    manager = backup_name
                    role = "backup"
                
                row_data = {
                    "id": int(contract.id),
                    "contract_id": str(contract.contract_id or ""),
                    "vendor_id": int(vendor_id) if vendor_id else 0,
                    "vendor_name": str(vendor_name or ""),
                    "contract_type": str(contract_type or ""),
                    "description": str(contract.contract_description or ""),
                    "expiration_date": str(formatted_date),
                    "expiration_timestamp": float(exp_timestamp),
                    "status": str(status or "Unknown"),
                    "manager": str(manager),
                    "role": str(role),
                }
                rows.append(row_data)
            
            print(f"Processed {len(rows)} contract rows")
            return rows
            
        except Exception as e:
            error_msg = f"Error fetching contracts: {str(e)}"
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

    # Fetch contracts data
    contract_rows = []
    
    # Initial fetch
    contract_rows = fetch_active_contracts()
    
    # Debug: Check if we have data
    print(f"Total contract rows fetched: {len(contract_rows)}")
    if contract_rows:
        print(f"First row sample: {contract_rows[0]}")
    else:
        ui.notify("No active contracts available. Please check the database.", type="warning")
    
    # Main container
    with ui.element("div").classes("max-w-6xl mt-8 mx-auto w-full"):
        # Section header with toggle
        with ui.row().classes('items-center justify-between ml-4 mb-4 w-full'):
            with ui.row().classes('items-center gap-2'):
                ui.icon('check_circle', color='green').style('font-size: 32px')
                ui.label("Active Contracts").classes("text-h5 font-bold")
            
            # Toggle for Owned/Backup
            role_toggle = ui.toggle(
                {'backup': 'Backup', 'owned': 'Owned'}, 
                value='backup', 
                on_change=on_role_toggle
            ).props('toggle-color=primary text-color=primary').classes('role-toggle')
        
        # Manager name and description row
        with ui.row().classes('items-center justify-between ml-4 mb-4 w-full'):
            ui.label("Contracts currently in effect").classes(
                "text-sm text-gray-500"
            )
            manager_label = ui.label("Manager: John Doe").classes(
                "text-base font-semibold text-primary"
            )
        
        # Count label row
        with ui.row().classes('ml-4 mb-2'):
            count_label = ui.label(f"Total: {len(contract_rows)} contracts").classes("text-sm text-gray-500")
        
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
        
        # Show message if no data
        if not contract_rows:
            with ui.card().classes("w-full p-6"):
                ui.label("No active contracts found").classes("text-lg font-bold text-gray-500")
                ui.label("Please check that the backend has contract data.").classes("text-sm text-gray-400 mt-2")
        
        # Create table after search bar (showing backup contracts by default - John Doe)
        initial_rows = [row for row in contract_rows if row.get('role') == 'backup']
        print(f"Creating table with {len(initial_rows)} rows (filtered by role: backup)")
        
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
        
        # Refresh function (defined after table is created)
        def refresh_contracts():
            nonlocal contract_rows
            contract_rows = fetch_active_contracts()
            count_label.set_text(f"Total: {len(contract_rows)} contracts")
            # Reapply current filters
            filter_contracts()
            ui.notify(f"Refreshed: {len(contract_rows)} active contracts loaded", type="info")
        
        # Add refresh button
        ui.button("Refresh", icon="refresh", on_click=refresh_contracts).props('color=primary flat').classes('ml-4')
        
        search_input.on_value_change(filter_contracts)
        
        # Add custom CSS for visual highlighting and toggle styling
        ui.add_css("""
            .contracts-table thead tr {
                background-color: #144c8e !important;
            }
            .contracts-table tbody tr {
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
        
        # Add slot for vendor name with clickable link (links to vendor details)
        contracts_table.add_slot('body-cell-vendor_name', '''
            <q-td :props="props">
                <a :href="'/vendor-info/' + props.row.vendor_id" class="text-blue-600 hover:text-blue-800 underline cursor-pointer">
                    {{ props.value }}
                </a>
            </q-td>
        ''')
        
        # Add slot for status column with normal text
        contracts_table.add_slot('body-cell-status', '''
            <q-td :props="props">
                <div class="text-gray-700">
                    {{ props.value }}
                </div>
            </q-td>
        ''')
