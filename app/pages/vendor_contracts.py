from datetime import datetime, date
from nicegui import ui
from app.db.database import SessionLocal
from app.services.contract_service import ContractService
from app.models.contract import ContractStatusType, ContractType, DepartmentType
from sqlalchemy.orm import joinedload
import base64
import os


def vendor_contracts(vendor_id: int):
    """Display all contracts for a specific vendor with filtering, search, and pagination"""
    
    # Fetch vendor and contracts from database
    vendor = None
    contracts = []
    db = SessionLocal()
    try:
        from app.models.vendor import Vendor
        from app.models.contract import Contract
        
        vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
        
        if vendor:
            # Load contracts with all relationships
            contracts = db.query(Contract).options(
                joinedload(Contract.vendor),
                joinedload(Contract.contract_owner),
                joinedload(Contract.contract_owner_backup),
                joinedload(Contract.contract_owner_manager),
                joinedload(Contract.documents)
            ).filter(Contract.vendor_id == vendor_id).all()
    except Exception as e:
        print(f"Error loading vendor contracts: {e}")
        import traceback
        traceback.print_exc()
        ui.notify(f"Error loading contracts: {e}", type="negative")
    finally:
        db.close()
    
    if not vendor:
        with ui.card().classes("w-full max-w-3xl mx-auto mt-4 p-6"):
            ui.label("Vendor not found").classes("text-red-600")
            with ui.link(target='/vendors').classes('no-underline'):
                ui.button("Back to Vendors List", icon="arrow_back").props('flat color=primary')
        return
    
    # Navigation
    with ui.row().classes("max-w-6xl mx-auto mt-4"):
        with ui.link(target=f'/vendor-info/{vendor_id}').classes('no-underline'):
            ui.button("Back to Vendor Profile", icon="arrow_back").props('flat color=primary')
    
    # Main container
    with ui.element("div").classes("max-w-6xl mt-8 mx-auto w-full"):
        # Header
        with ui.row().classes('items-center justify-between ml-4 mb-4 w-full'):
            with ui.row().classes('items-center gap-2'):
                ui.icon('description', color='blue').style('font-size: 32px')
                ui.label(f"Contracts - {vendor.vendor_name}").classes("text-h5 font-bold")
        
        # Prepare contract rows data
        contract_rows = []
        for contract in contracts:
            owner_name = f"{contract.contract_owner.first_name} {contract.contract_owner.last_name}" if contract.contract_owner else "N/A"
            backup_name = f"{contract.contract_owner_backup.first_name} {contract.contract_owner_backup.last_name}" if contract.contract_owner_backup else "N/A"
            manager_name = f"{contract.contract_owner_manager.first_name} {contract.contract_owner_manager.last_name}" if contract.contract_owner_manager else "N/A"
            
            contract_type = contract.contract_type.value if hasattr(contract.contract_type, 'value') else str(contract.contract_type)
            department = contract.department.value if hasattr(contract.department, 'value') else str(contract.department)
            status = contract.status.value if hasattr(contract.status, 'value') else str(contract.status)
            
            # Determine status color
            if contract.status == ContractStatusType.ACTIVE:
                status_color = "green"
            elif contract.status == ContractStatusType.TERMINATED:
                status_color = "black"
            elif contract.status == ContractStatusType.EXPIRED:
                status_color = "red"
            elif contract.status == ContractStatusType.PENDING_TERMINATION:
                status_color = "yellow"
            else:
                status_color = "gray"
            
            start_date_str = contract.start_date.strftime("%Y-%m-%d") if contract.start_date else "N/A"
            end_date_str = contract.end_date.strftime("%Y-%m-%d") if contract.end_date else "N/A"
            
            row_data = {
                "id": int(contract.id),
                "contract_id": str(contract.contract_id or ""),
                "vendor_name": str(vendor.vendor_name),
                "contract_type": str(contract_type),
                "description": str(contract.contract_description or ""),
                "department": str(department),
                "owner": str(owner_name),
                "backup": str(backup_name),
                "manager": str(manager_name),
                "start_date": str(start_date_str),
                "expiration_date": str(end_date_str),
                "status": str(status),
                "status_color": str(status_color),
            }
            contract_rows.append(row_data)
        
        # Store contracts in a separate lookup dictionary (not in row data to avoid JSON serialization issues)
        contracts_lookup = {contract.id: contract for contract in contracts}
        
        # Filter and search state
        filtered_rows = contract_rows.copy()
        
        # Make contracts_lookup available in the scope where it's needed
        # (it's already in scope, but we'll reference it explicitly)
        
        # Table columns
        contract_columns = [
            {"name": "contract_id", "label": "Contract ID", "field": "contract_id", "align": "left", "sortable": True},
            {"name": "contract_type", "label": "Type", "field": "contract_type", "align": "left", "sortable": True},
            {"name": "description", "label": "Description", "field": "description", "align": "left", "sortable": True},
            {"name": "department", "label": "Department", "field": "department", "align": "left", "sortable": True},
            {"name": "owner", "label": "Contract Manager", "field": "owner", "align": "left", "sortable": True},
            {"name": "backup", "label": "Backup", "field": "backup", "align": "left", "sortable": True},
            {"name": "manager", "label": "Owner", "field": "manager", "align": "left", "sortable": True},
            {"name": "start_date", "label": "Start Date", "field": "start_date", "align": "left", "sortable": True},
            {"name": "expiration_date", "label": "Expiration Date", "field": "expiration_date", "align": "left", "sortable": True},
            {"name": "status", "label": "Status", "field": "status", "align": "left", "sortable": True},
        ]
        
        contract_columns_defaults = {
            "align": "left",
            "headerClasses": "bg-[#144c8e] text-white",
        }
        
        # Filters and search UI
        with ui.card().classes("w-full mb-4 p-4"):
            ui.label("Filters & Search").classes("text-lg font-bold mb-3")
            
            # Search input
            with ui.row().classes('w-full mb-4 gap-2'):
                search_input = ui.input(
                    placeholder='Search by Contract ID, Type, Description, Department, Owner...'
                ).classes('flex-1').props('outlined dense clearable')
                with search_input.add_slot('prepend'):
                    ui.icon('search').classes('text-gray-400')
            
            # Filter row
            with ui.row().classes('w-full gap-4 flex-wrap'):
                # Status filter
                status_filter = ui.select(
                    options=[
                        {"label": "All Statuses", "value": None},
                        {"label": "Active", "value": "Active"},
                        {"label": "Expired", "value": "Expired"},
                        {"label": "Terminated", "value": "Terminated"},
                        {"label": "Pending Termination", "value": "Pending Termination"},
                    ],
                    value=None,
                    label="Status"
                ).classes('flex-1 min-w-[150px]').props('outlined dense')
                
                # Type filter
                type_options = [{"label": "All Types", "value": None}]
                type_options.extend([{"label": ct.value, "value": ct.value} for ct in ContractType])
                type_filter = ui.select(
                    options=type_options,
                    value=None,
                    label="Type"
                ).classes('flex-1 min-w-[150px]').props('outlined dense')
                
                # Department filter
                dept_options = [{"label": "All Departments", "value": None}]
                dept_options.extend([{"label": dept.value, "value": dept.value} for dept in DepartmentType])
                department_filter = ui.select(
                    options=dept_options,
                    value=None,
                    label="Department"
                ).classes('flex-1 min-w-[150px]').props('outlined dense')
                
                # Owner filter (get unique owners from contracts)
                owner_options = [{"label": "All Owners", "value": None}]
                unique_owners = sorted(set([row["owner"] for row in contract_rows if row["owner"] != "N/A"]))
                owner_options.extend([{"label": owner, "value": owner} for owner in unique_owners])
                owner_filter = ui.select(
                    options=owner_options,
                    value=None,
                    label="Owner"
                ).classes('flex-1 min-w-[150px]').props('outlined dense')
            
            # Action buttons
            with ui.row().classes('w-full gap-2 mt-2'):
                filter_btn = ui.button("Apply Filters", icon="filter_list").props('color=primary')
                clear_btn = ui.button("Clear Filters", icon="clear").props('color=secondary')
        
        # Count label
        count_label = ui.label(f"Total: {len(contract_rows)} contract(s)").classes("text-sm text-gray-500 ml-4 mb-2")
        
        # Pagination size selector
        with ui.row().classes('items-center gap-2 ml-4 mb-2'):
            ui.label("Items per page:").classes("text-sm")
            page_size_select = ui.select(
                options=[10, 25, 50, 100],
                value=10,
                label=""
            ).props('outlined dense').classes('w-20')
        
        # Filter and search function
        def apply_filters():
            nonlocal filtered_rows
            filtered_rows = contract_rows.copy()
            
            # Apply status filter
            if status_filter.value:
                filtered_rows = [r for r in filtered_rows if r["status"] == status_filter.value]
            
            # Apply type filter
            if type_filter.value:
                filtered_rows = [r for r in filtered_rows if r["contract_type"] == type_filter.value]
            
            # Apply department filter
            if department_filter.value:
                filtered_rows = [r for r in filtered_rows if r["department"] == department_filter.value]
            
            # Apply owner filter
            if owner_filter.value:
                filtered_rows = [r for r in filtered_rows if r["owner"] == owner_filter.value]
            
            # Apply search
            search_term = (search_input.value or "").lower()
            if search_term:
                filtered_rows = [
                    r for r in filtered_rows
                    if search_term in (r.get('contract_id', '') or "").lower()
                    or search_term in (r.get('contract_type', '') or "").lower()
                    or search_term in (r.get('description', '') or "").lower()
                    or search_term in (r.get('department', '') or "").lower()
                    or search_term in (r.get('owner', '') or "").lower()
                    or search_term in (r.get('backup', '') or "").lower()
                    or search_term in (r.get('manager', '') or "").lower()
                ]
            
            # Update count
            count_label.set_text(f"Showing: {len(filtered_rows)} of {len(contract_rows)} contract(s)")
            
            # Update table
            contracts_table.rows = filtered_rows
            contracts_table.pagination = page_size_select.value
            contracts_table.update()
        
        def clear_filters():
            status_filter.value = None
            type_filter.value = None
            department_filter.value = None
            owner_filter.value = None
            search_input.value = ""
            apply_filters()
        
        # Bind filter events
        filter_btn.on_click(apply_filters)
        clear_btn.on_click(clear_filters)
        search_input.on_value_change(apply_filters)
        page_size_select.on_value_change(lambda: apply_filters())
        
        # Contract details dialog
        with ui.dialog() as contract_details_dialog, ui.card().classes("min-w-[900px] max-w-5xl max-h-[90vh] overflow-y-auto"):
            ui.label("Contract Details").classes("text-h5 mb-4 text-blue-600 font-bold")
            
            details_container = ui.column().classes("w-full")
            
            # View/Download document handlers
            def make_download_handler(doc_path, doc_name, file_name):
                def download_document():
                    if os.path.exists(doc_path):
                        with open(doc_path, 'rb') as f:
                            file_content = f.read()
                        b64_content = base64.b64encode(file_content).decode()
                        ui.run_javascript(f'''
                            const link = document.createElement('a');
                            link.href = 'data:application/pdf;base64,{b64_content}';
                            link.download = '{file_name}';
                            document.body.appendChild(link);
                            link.click();
                            document.body.removeChild(link);
                        ''')
                        ui.notify(f"Downloaded {doc_name}", type="positive")
                    else:
                        ui.notify(f"File not found: {doc_name}", type="negative")
                return download_document
            
            def show_contract_details(contract_obj):
                details_container.clear()
                with details_container:
                    contract = contract_obj
                    
                    # Basic Information
                    with ui.card().classes("w-full mb-4 p-4 border-l-4 border-blue-400"):
                        ui.label("Basic Information").classes("text-lg font-bold mb-3")
                        with ui.grid(columns=2).classes("gap-4 w-full"):
                            ui.label(f"Contract ID: {contract.contract_id}").classes("font-semibold")
                            ui.label(f"Vendor: {contract.vendor.vendor_name if contract.vendor else 'N/A'}").classes("font-semibold")
                            ui.label(f"Type: {contract.contract_type.value if hasattr(contract.contract_type, 'value') else contract.contract_type}").classes("font-semibold")
                            ui.label(f"Department: {contract.department.value if hasattr(contract.department, 'value') else contract.department}").classes("font-semibold")
                            ui.label(f"Description: {contract.contract_description}").classes("font-semibold")
                            
                            # Status with color
                            status_val = contract.status.value if hasattr(contract.status, 'value') else str(contract.status)
                            if contract.status == ContractStatusType.ACTIVE:
                                ui.badge(status_val, color="green").classes("text-sm font-semibold")
                            elif contract.status == ContractStatusType.TERMINATED:
                                ui.badge(status_val, color="black").classes("text-sm font-semibold")
                            elif contract.status == ContractStatusType.EXPIRED:
                                ui.badge(status_val, color="red").classes("text-sm font-semibold")
                            elif contract.status == ContractStatusType.PENDING_TERMINATION:
                                ui.badge(status_val, color="yellow").classes("text-sm font-semibold")
                            else:
                                ui.label(f"Status: {status_val}").classes("font-semibold")
                    
                    # Dates
                    with ui.card().classes("w-full mb-4 p-4 border-l-4 border-green-400"):
                        ui.label("Dates").classes("text-lg font-bold mb-3")
                        with ui.grid(columns=2).classes("gap-4 w-full"):
                            ui.label(f"Start Date: {contract.start_date.strftime('%Y-%m-%d') if contract.start_date else 'N/A'}")
                            ui.label(f"Expiration Date: {contract.end_date.strftime('%Y-%m-%d') if contract.end_date else 'N/A'}")
                    
                    # Contract Management
                    with ui.card().classes("w-full mb-4 p-4 border-l-4 border-purple-400"):
                        ui.label("Contract Management").classes("text-lg font-bold mb-3")
                        with ui.grid(columns=2).classes("gap-4 w-full"):
                            owner_name = f"{contract.contract_owner.first_name} {contract.contract_owner.last_name}" if contract.contract_owner else "N/A"
                            backup_name = f"{contract.contract_owner_backup.first_name} {contract.contract_owner_backup.last_name}" if contract.contract_owner_backup else "N/A"
                            manager_name = f"{contract.contract_owner_manager.first_name} {contract.contract_owner_manager.last_name}" if contract.contract_owner_manager else "N/A"
                            ui.label(f"Contract Manager: {owner_name}")
                            ui.label(f"Backup: {backup_name}")
                            ui.label(f"Owner: {manager_name}")
                    
                    # Financial Information
                    with ui.card().classes("w-full mb-4 p-4 border-l-4 border-orange-400"):
                        ui.label("Financial Information").classes("text-lg font-bold mb-3")
                        with ui.grid(columns=2).classes("gap-4 w-full"):
                            ui.label(f"Amount: {contract.contract_currency.value if hasattr(contract.contract_currency, 'value') else contract.contract_currency} {contract.contract_amount:,.2f}")
                            ui.label(f"Payment Method: {contract.payment_method.value if hasattr(contract.payment_method, 'value') else contract.payment_method}")
                    
                    # Renewal Information
                    with ui.card().classes("w-full mb-4 p-4 border-l-4 border-yellow-400"):
                        ui.label("Renewal Information").classes("text-lg font-bold mb-3")
                        with ui.grid(columns=2).classes("gap-4 w-full"):
                            ui.label(f"Automatic Renewal: {contract.automatic_renewal.value if hasattr(contract.automatic_renewal, 'value') else contract.automatic_renewal}")
                            if contract.renewal_period:
                                ui.label(f"Renewal Period: {contract.renewal_period.value if hasattr(contract.renewal_period, 'value') else contract.renewal_period}")
                    
                    # Documents
                    if contract.documents:
                        with ui.card().classes("w-full mb-4 p-4 border-l-4 border-indigo-400"):
                            ui.label("Contract Documents").classes("text-lg font-bold mb-3")
                            for doc in contract.documents:
                                with ui.row().classes("items-center gap-4 p-2 bg-gray-50 rounded mb-2 w-full"):
                                    ui.label(doc.custom_document_name or doc.file_name).classes("flex-1 font-medium")
                                    ui.label(f"Issue Date: {doc.document_signed_date.strftime('%Y-%m-%d') if doc.document_signed_date else 'N/A'}").classes("text-sm text-gray-600")
                                    view_btn = ui.button("View", icon="visibility").props('color=primary flat size=sm')
                                    download_btn = ui.button("Download", icon="download").props('color=secondary flat size=sm')
                                    
                                    def make_view_handler(doc_path, doc_name, file_name):
                                        def view_document():
                                            make_download_handler(doc_path, doc_name, file_name)()
                                        return view_document
                                    
                                    view_btn.on_click(make_view_handler(doc.file_path, doc.custom_document_name, doc.file_name))
                                    download_btn.on_click(make_download_handler(doc.file_path, doc.custom_document_name, doc.file_name))
            
            # Close button
            with ui.row().classes("justify-end mt-4 w-full"):
                ui.button("Close", icon="close", on_click=contract_details_dialog.close).props('color=primary')
        
        # Create table
        contracts_table = ui.table(
            columns=contract_columns,
            column_defaults=contract_columns_defaults,
            rows=filtered_rows,
            pagination=page_size_select.value,
            row_key="id"
        ).classes("w-full").props("flat bordered").classes("shadow-lg rounded-lg overflow-hidden")
        
        # Add clickable contract ID column
        contracts_table.add_slot('body-cell-contract_id', '''
            <q-td :props="props">
                <a href="#" @click.prevent="window.vendorContractsShowDetails(props.row.id)" class="text-blue-600 hover:text-blue-800 underline cursor-pointer">
                    {{ props.value }}
                </a>
            </q-td>
        ''')
        
        # Add status color slot
        contracts_table.add_slot('body-cell-status', '''
            <q-td :props="props">
                <div v-if="props.row.status_color === 'green'" class="text-green-700 font-semibold">
                    {{ props.value }}
                </div>
                <div v-else-if="props.row.status_color === 'black'" class="text-black font-semibold">
                    {{ props.value }}
                </div>
                <div v-else-if="props.row.status_color === 'red'" class="text-red-700 font-semibold">
                    {{ props.value }}
                </div>
                <div v-else-if="props.row.status_color === 'yellow'" class="text-yellow-700 font-semibold">
                    {{ props.value }}
                </div>
                <div v-else class="text-gray-700 font-semibold">
                    {{ props.value }}
                </div>
            </q-td>
        ''')
        
        # Store contract lookup using contracts_lookup dictionary (not from row data)
        # Note: contracts_lookup is defined earlier when we process contracts
        
        # Add Actions column
        contract_columns.append({
            "name": "actions",
            "label": "Actions",
            "field": "actions",
            "align": "center",
            "sortable": False
        })
        
        # Global variable to store pending contract view ID
        pending_contract_id = {'value': None}
        
        # Add actions slot with View button
        contracts_table.add_slot('body-cell-actions', '''
            <q-td :props="props">
                <q-btn flat dense color="primary" icon="visibility" label="View" 
                       @click="window.pendingContractViewId = props.row.id" />
            </q-td>
        ''')
        
        # Update contract ID to be clickable
        contracts_table.add_slot('body-cell-contract_id', '''
            <q-td :props="props">
                <a href="#" class="text-blue-600 hover:text-blue-800 underline cursor-pointer" 
                   @click.prevent="window.pendingContractViewId = props.row.id">
                    {{ props.value }}
                </a>
            </q-td>
        ''')
        
        # Initialize JavaScript variable
        ui.run_javascript('window.pendingContractViewId = null;')
        
        # Poll for contract view requests
        def check_for_contract_view():
            try:
                result = ui.run_javascript('return window.pendingContractViewId;', timeout=0.1)
                if result and result != pending_contract_id['value']:
                    pending_contract_id['value'] = result
                    contract_id = int(result)
                    if contract_id in contracts_lookup:
                        show_contract_details(contracts_lookup[contract_id])
                        contract_details_dialog.open()
                        # Reset
                        ui.run_javascript('window.pendingContractViewId = null;')
                        pending_contract_id['value'] = None
            except:
                pass  # Ignore errors from JavaScript calls
        
        # Start polling timer
        ui.timer(0.2, check_for_contract_view)
        
        # Show "No results found" message
        if not filtered_rows:
            with ui.card().classes("w-full p-6 mt-4"):
                ui.label("No results found").classes("text-lg font-bold text-gray-500")
                ui.label("Try adjusting your search or filters.").classes("text-sm text-gray-400 mt-2")
        
        # Initial filter application
        apply_filters()

