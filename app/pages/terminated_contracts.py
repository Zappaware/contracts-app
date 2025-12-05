from datetime import datetime, timedelta
from nicegui import ui
import io
import base64
from app.utils.vendor_lookup import get_vendor_id_by_name
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


def terminated_contracts():
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
    
    # Mock data for terminated contracts
    def get_mock_terminated_contracts():
        """
        Simulates terminated contracts.
        This will be replaced with actual API call when available.
        """
        today = datetime.now()
        
        mock_contracts = [
            {
                "contract_id": "CTR-2023-001",
                "vendor_name": "Acme Corp",
                "contract_type": "Service Agreement",
                "description": "IT Support Services",
                "start_date": today - timedelta(days=730),  # 2 years ago
                "end_date": today - timedelta(days=120),
                "expiration_date": today - timedelta(days=120),
                "date_terminated": today - timedelta(days=120),
                "manager": "William Defoe",
                "backup": "John Doe",
                "department": "IT",
                "role": "owned"
            },
            {
                "contract_id": "CTR-2023-012",
                "vendor_name": "Beta Technologies",
                "contract_type": "Software License",
                "description": "Enterprise Software Licensing",
                "start_date": today - timedelta(days=365),  # 1 year ago
                "end_date": today - timedelta(days=90),
                "expiration_date": today - timedelta(days=90),
                "date_terminated": today - timedelta(days=90),
                "manager": "John Doe",
                "backup": "William Defoe",
                "department": "Operations",
                "role": "backup"
            },
            {
                "contract_id": "CTR-2023-023",
                "vendor_name": "Gamma Consulting",
                "contract_type": "Consulting",
                "description": "Business Process Optimization",
                "start_date": today - timedelta(days=600),  # ~1.6 years ago
                "end_date": today - timedelta(days=200),
                "expiration_date": today - timedelta(days=200),
                "date_terminated": today - timedelta(days=200),
                "manager": "William Defoe",
                "backup": "John Doe",
                "department": "Strategy",
                "role": "owned"
            },
            {
                "contract_id": "CTR-2023-034",
                "vendor_name": "Delta Logistics",
                "contract_type": "Transportation",
                "description": "Freight and Delivery Services",
                "start_date": today - timedelta(days=180),  # 6 months ago
                "end_date": today - timedelta(days=45),
                "expiration_date": today - timedelta(days=45),
                "date_terminated": today - timedelta(days=45),
                "manager": "John Doe",
                "backup": "William Defoe",
                "department": "Logistics",
                "role": "backup"
            },
            {
                "contract_id": "CTR-2022-089",
                "vendor_name": "Epsilon Security",
                "contract_type": "Security Services",
                "description": "Building Security and Monitoring",
                "start_date": today - timedelta(days=1095),  # 3 years ago
                "end_date": today - timedelta(days=300),
                "expiration_date": today - timedelta(days=300),
                "date_terminated": today - timedelta(days=300),
                "manager": "William Defoe",
                "backup": "John Doe",
                "department": "Security",
                "role": "owned"
            },
            {
                "contract_id": "CTR-2023-045",
                "vendor_name": "Zeta Solutions",
                "contract_type": "Maintenance",
                "description": "Equipment Maintenance Contract",
                "start_date": today - timedelta(days=450),  # ~1.2 years ago
                "end_date": today - timedelta(days=150),
                "expiration_date": today - timedelta(days=150),
                "date_terminated": today - timedelta(days=150),
                "manager": "John Doe",
                "backup": "William Defoe",
                "department": "Facilities",
                "role": "backup"
            },
            {
                "contract_id": "CTR-2023-056",
                "vendor_name": "Eta Services",
                "contract_type": "Cleaning Services",
                "description": "Office Cleaning and Janitorial",
                "start_date": today - timedelta(days=240),  # 8 months ago
                "end_date": today - timedelta(days=60),
                "expiration_date": today - timedelta(days=60),
                "date_terminated": today - timedelta(days=60),
                "manager": "William Defoe",
                "backup": "John Doe",
                "department": "Facilities",
                "role": "owned"
            },
            {
                "contract_id": "CTR-2023-067",
                "vendor_name": "Theta Communications",
                "contract_type": "Telecommunications",
                "description": "Internet and Phone Services",
                "start_date": today - timedelta(days=540),  # ~1.5 years ago
                "end_date": today - timedelta(days=180),
                "expiration_date": today - timedelta(days=180),
                "date_terminated": today - timedelta(days=180),
                "manager": "John Doe",
                "backup": "William Defoe",
                "department": "IT",
                "role": "backup"
            },
        ]
        
        rows = []
        for contract in mock_contracts:
            exp_date = contract["expiration_date"]
            start_date = contract["start_date"]
            end_date = contract["end_date"]
            date_terminated = contract["date_terminated"]
            
            # Look up vendor_id from vendor_name
            vendor_id = get_vendor_id_by_name(contract["vendor_name"])
            
            rows.append({
                "contract_id": contract["contract_id"],
                "vendor_name": contract["vendor_name"],
                "vendor_id": vendor_id,  # Add vendor_id for routing
                "contract_type": contract["contract_type"],
                "description": contract["description"],
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "expiration_date": exp_date.strftime("%Y-%m-%d"),
                "expiration_timestamp": exp_date.timestamp(),  # For sorting
                "date_terminated": date_terminated.strftime("%Y-%m-%d"),
                "date_terminated_timestamp": date_terminated.timestamp(),  # For sorting
                "status": "Terminated",
                "manager": contract["manager"],
                "backup": contract["backup"],
                "department": contract["department"],
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

    contract_rows = get_mock_terminated_contracts()
    
    # Main container
    with ui.element("div").classes("max-w-6xl mt-8 mx-auto w-full"):
        # Section header with toggle and Generate button
        with ui.row().classes('items-center justify-between ml-4 mb-4 w-full'):
            with ui.row().classes('items-center gap-2'):
                ui.icon('cancel', color='grey').style('font-size: 32px')
                ui.label("Terminated Contracts").classes("text-h5 font-bold")
            
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
            ui.label("Contracts that have been terminated").classes(
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
        
        # Add slot for vendor name with clickable link
        contracts_table.add_slot('body-cell-vendor_name', '''
            <q-td :props="props">
                <a v-if="props.row.vendor_id" :href="'/vendor-info/' + props.row.vendor_id" class="text-blue-600 hover:text-blue-800 underline cursor-pointer">
                    {{ props.value }}
                </a>
                <span v-else class="text-gray-600">{{ props.value }}</span>
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
        
        # Function to generate Excel report
        def open_generate_dialog():
            """Open dialog for date range selection and report generation"""
            with ui.dialog() as dialog, ui.card().classes('p-6 w-full max-w-md'):
                ui.label("Generate Terminated Contracts Report").classes("text-h6 font-bold mb-4")
                
                with ui.column().classes('gap-4 w-full'):
                    ui.label("Select date range for terminated contracts:").classes("text-sm text-gray-600")
                    
                    start_date_input = ui.input("Start Date", placeholder="YYYY-MM-DD").props('type=date').classes('w-full')
                    end_date_input = ui.input("End Date", placeholder="YYYY-MM-DD").props('type=date').classes('w-full')
                    
                    # Set default dates (last 6 months)
                    today = datetime.now()
                    default_start = (today - timedelta(days=180)).strftime("%Y-%m-%d")
                    default_end = today.strftime("%Y-%m-%d")
                    start_date_input.value = default_start
                    end_date_input.value = default_end
                    
                    ui.label("The report will include all contracts with status 'Terminated' within the selected date range.").classes("text-xs text-gray-500 italic")
                    
                    with ui.row().classes('gap-2 justify-end w-full mt-4'):
                        ui.button("Cancel", on_click=dialog.close).props('flat')
                        ui.button("Generate & Download", icon="download", 
                                 on_click=lambda: generate_excel_report(start_date_input.value, end_date_input.value, dialog)).props('color=primary')
                
                dialog.open()
        
        def generate_excel_report(start_date_str, end_date_str, dialog):
            """Generate Excel report for terminated contracts within date range"""
            try:
                # Parse dates
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
                
                if start_date > end_date:
                    ui.notify("Start date must be before end date", type="negative")
                    return
                
                # Filter contracts by date range and status
                filtered_contracts = []
                for row in contract_rows:
                    if row.get('status') == 'Terminated':
                        terminated_date_str = row.get('date_terminated', '')
                        if terminated_date_str:
                            try:
                                terminated_date = datetime.strptime(terminated_date_str, "%Y-%m-%d")
                                if start_date <= terminated_date <= end_date:
                                    filtered_contracts.append(row)
                            except ValueError:
                                continue
                
                if not filtered_contracts:
                    ui.notify("No terminated contracts found in the selected date range", type="warning")
                    dialog.close()
                    return
                
                if not PANDAS_AVAILABLE:
                    ui.notify("Excel export requires pandas library. Please install it: pip install pandas openpyxl", type="negative")
                    dialog.close()
                    return
                
                # Prepare data for Excel
                report_data = []
                for contract in filtered_contracts:
                    report_data.append({
                        "Contract ID": contract.get('contract_id', ''),
                        "Contract Type": contract.get('contract_type', ''),
                        "Description": contract.get('description', ''),
                        "Vendor": contract.get('vendor_name', ''),
                        "Start Date": contract.get('start_date', ''),
                        "End Date": contract.get('end_date', ''),
                        "Department": contract.get('department', ''),
                        "Contract Manager": contract.get('manager', ''),
                        "Contract Backups": contract.get('backup', ''),
                        "Date Terminated in system": contract.get('date_terminated', ''),
                    })
                
                # Create DataFrame
                df = pd.DataFrame(report_data)
                
                # Create Excel file in memory
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Terminated Contracts')
                    
                    # Get the worksheet
                    worksheet = writer.sheets['Terminated Contracts']
                    
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
                filename = f"Terminated_Contracts_Report_{start_date_str}_to_{end_date_str}.xlsx"
                
                # Trigger download using JavaScript
                ui.run_javascript(f'''
                    const link = document.createElement('a');
                    link.href = 'data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64_data}';
                    link.download = '{filename}';
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                ''')
                
                ui.notify(f"Report generated successfully! {len(filtered_contracts)} contract(s) exported.", type="positive")
                dialog.close()
                
            except ValueError:
                ui.notify("Invalid date format. Please use YYYY-MM-DD format.", type="negative")
            except Exception as e:
                ui.notify(f"Error generating report: {str(e)}", type="negative")
                import traceback
                traceback.print_exc()
