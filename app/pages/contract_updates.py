from datetime import datetime, timedelta
from nicegui import ui
import io
import base64
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


def contract_updates():
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
        
        # Update manager name based on role
        if role == 'backup':
            manager_name = "John Doe"
            ui.notify("Showing backup contracts (John Doe)", type="info")
        else:  # owned
            manager_name = "William Defoe"
            ui.notify("Showing owned contracts (William Defoe)", type="info")
        
        # Update the manager label
        manager_label.set_text(f"Manager: {manager_name}")
        
        # Reapply filters
        apply_filters()
    
    # Mock data for contract updates (contracts with responses from managers)
    def get_mock_contract_updates():
        """
        Simulates contracts that have received responses from Contract Managers or Backups.
        Includes both new responses (pending approval) and returned responses (after corrections).
        This will be replaced with actual API call when available.
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
                "returned_reason": None
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
                "correction_date": today - timedelta(days=1)
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
                "correction_date": today - timedelta(days=5)
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
                "returned_reason": None
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
                "returned_reason": None
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
                "returned_reason": None
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
            
            row_data = {
                "contract_id": contract["contract_id"],
                "vendor_name": contract["vendor_name"],
                "contract_type": contract["contract_type"],
                "description": contract["description"],
                "expiration_date": exp_date.strftime("%Y-%m-%d"),
                "expiration_timestamp": exp_date.timestamp(),  # For sorting
                "manager": contract["manager"],
                "role": contract["role"],
                "response_provided_by": contract["response_provided_by"],
                "response_date": contract["response_date"].strftime("%Y-%m-%d"),
                "has_document": contract["has_document"],
                "status": contract["status"],  # "pending_approval" or "returned"
                "previous_response": contract.get("previous_response"),
                "returned_reason": contract.get("returned_reason"),
                "returned_date": contract.get("returned_date").strftime("%Y-%m-%d") if contract.get("returned_date") else None,
                "correction_date": contract.get("correction_date").strftime("%Y-%m-%d") if contract.get("correction_date") else None,
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
            "name": "manager",
            "label": "Contract Owner",
            "field": "manager",
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

    contract_rows = get_mock_contract_updates()
    
    # Filter dropdowns
    owner_filter = None
    vendor_filter = None
    type_filter = None
    status_filter = None
    search_input = None
    
    # Main container
    with ui.element("div").classes("max-w-6xl mt-8 mx-auto w-full"):
        # Section header with toggle and Generate button
        with ui.row().classes('items-center justify-between ml-4 mb-4 w-full'):
            with ui.row().classes('items-center gap-2'):
                ui.icon('update', color='primary').style('font-size: 32px')
                ui.label("Contract Updates").classes("text-h5 font-bold")
            
            with ui.row().classes('items-center gap-3'):
                # Generate Report button
                ui.button("Generate", icon="description", on_click=lambda: open_generate_dialog()).props('color=primary')
                
                # Toggle for Owned/Backup
                role_toggle = ui.toggle(
                    {'backup': 'Backup', 'owned': 'Owned'}, 
                    value='backup', 
                    on_change=on_role_toggle
                ).props('toggle-color=primary text-color=primary').classes('role-toggle')
        
        # Manager name and description row
        with ui.row().classes('items-center justify-between ml-4 mb-4 w-full'):
            ui.label("Review responses provided by Contract Managers or Backups").classes(
                "text-sm text-gray-500"
            )
            manager_label = ui.label("Manager: John Doe").classes(
                "text-base font-semibold text-primary"
            )
        
        # Filter section with dropdowns
        with ui.row().classes('w-full ml-4 mr-4 mb-4 gap-4 px-2 flex-wrap'):
            # Contract Owner filter
            with ui.column().classes('flex-1 min-w-[200px]'):
                ui.label("Filter by Contract Owner:").classes("text-sm font-medium mb-1")
                owner_filter = ui.select(
                    options=['All', 'William Defoe', 'John Doe'],
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
                    options=['All', 'Returned', 'Updated'],
                    value='All',
                    on_change=lambda e: apply_filters()
                ).classes('w-full').props('outlined dense')
        
        # Define filter function
        def apply_filters():
            # Get base rows based on current toggle state
            current_role = role_toggle.value
            base_rows = [row for row in contract_rows if row['role'] == current_role]
            
            # Apply owner filter
            if owner_filter.value and owner_filter.value != 'All':
                base_rows = [row for row in base_rows if row['manager'] == owner_filter.value]
            
            # Apply vendor filter
            if vendor_filter.value and vendor_filter.value != 'All':
                base_rows = [row for row in base_rows if row['vendor_name'] == vendor_filter.value]
            
            # Apply type filter
            if type_filter.value and type_filter.value != 'All':
                base_rows = [row for row in base_rows if row['contract_type'] == type_filter.value]
            
            # Apply status filter
            if status_filter.value and status_filter.value != 'All':
                if status_filter.value == 'Returned':
                    base_rows = [row for row in base_rows if row.get('status') == 'returned']
                elif status_filter.value == 'Updated':
                    base_rows = [row for row in base_rows if row.get('status') == 'updated']
            
            # Apply search filter (including status)
            search_term = (search_input.value or "").lower()
            if search_term:
                base_rows = [
                    row for row in base_rows
                    if search_term in (row['contract_id'] or "").lower()
                    or search_term in (row['vendor_name'] or "").lower()
                    or search_term in (row['contract_type'] or "").lower()
                    or search_term in (row['description'] or "").lower()
                    or search_term in (row['manager'] or "").lower()
                    or search_term in (row.get('status', '') or "").lower()
                    or (search_term == 'returned' and row.get('status') == 'returned')
                    or (search_term == 'updated' and row.get('status') == 'updated')
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
        
        search_input.on_value_change(apply_filters)
        
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
        
        # Add slot for status column with visual distinction
        contracts_table.add_slot('body-cell-status', '''
            <q-td :props="props">
                <div v-if="props.row.status === 'returned'" class="flex items-center justify-center">
                    <q-btn 
                        label="Returned" 
                        color="negative" 
                        size="sm" 
                        icon="undo"
                        dense
                        class="font-semibold"
                    />
                </div>
                <div v-else-if="props.row.status === 'updated'" class="flex items-center justify-center">
                    <q-btn 
                        label="Updated" 
                        color="positive" 
                        size="sm" 
                        icon="check_circle"
                        dense
                        class="font-semibold"
                    />
                </div>
                <div v-else class="flex items-center justify-center">
                    <q-badge 
                        color="grey" 
                        :label="props.row.status"
                        class="font-semibold"
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
                if row.get('status') == 'returned' and row.get('previous_response'):
                    with ui.card().classes('p-3 bg-blue-50 border border-blue-200 mb-4'):
                        ui.label("Note: Previous information and documents are retained if unchanged.").classes("text-sm text-blue-700")
                
                with ui.column().classes('gap-4 w-full'):
                    contract_id_input = ui.input("Contract ID", value=row['contract_id']).classes('w-full')
                    vendor_input = ui.input("Vendor Name", value=row['vendor_name']).classes('w-full')
                    type_input = ui.input("Contract Type", value=row['contract_type']).classes('w-full')
                    description_input = ui.textarea("Description", value=row['description']).classes('w-full')
                    expiration_input = ui.input("Expiration Date", value=row['expiration_date']).props('type=date').classes('w-full')
                    manager_input = ui.input("Contract Owner", value=row['manager']).classes('w-full')
                    
                    # Show previous values if this is a returned contract
                    if row.get('status') == 'returned' and row.get('previous_response'):
                        ui.separator()
                        ui.label("Previous Values (for reference):").classes("text-sm font-semibold text-gray-600")
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
            # TODO: Implement API call to save changes
            # Update the row data with new values
            for key, value in new_data.items():
                if key in original_row:
                    original_row[key] = value
            ui.notify(f"Changes saved for contract {original_row['contract_id']}", type="positive")
            dialog.close()
            # Refresh table
            apply_filters()
        
        def complete_contract(row):
            """Complete and approve contract update"""
            with ui.dialog() as dialog, ui.card().classes('p-6'):
                ui.label("Complete Contract Update").classes("text-h6 font-bold mb-4")
                ui.label(f"Are you sure you want to complete and approve the update for contract {row['contract_id']}?").classes("mb-4")
                
                with ui.row().classes('gap-2 justify-end'):
                    ui.button("Cancel", on_click=dialog.close).props('flat')
                    ui.button("Complete", icon="check_circle", on_click=lambda: confirm_complete(row, dialog)).props('color=positive')
                
                dialog.open()
        
        def confirm_complete(row, dialog):
            """Confirm completion"""
            # TODO: Implement API call to complete contract
            ui.notify(f"Contract {row['contract_id']} has been completed and approved", type="positive")
            dialog.close()
            # Remove from list (or mark as completed)
            contract_rows[:] = [r for r in contract_rows if r['contract_id'] != row['contract_id']]
            apply_filters()
        
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
        contract_data_map = {row['contract_id']: row for row in contract_rows}
        
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
                    
                    ui.label("Actions:").classes("text-base font-semibold mt-2")
                    with ui.column().classes('gap-2 w-full'):
                        ui.button("Edit Information", icon="edit", on_click=lambda: [edit_contract_info(row, dialog), dialog.close()]).props('color=secondary full-width')
                        ui.button("Complete", icon="check_circle", on_click=lambda: [complete_contract(row), dialog.close()]).props('color=positive full-width')
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

