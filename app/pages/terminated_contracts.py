from datetime import datetime, timedelta
from nicegui import ui, app
import io
import base64
from app.db.database import SessionLocal
from app.models.contract import User
from app.services.contract_service import ContractService
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


def terminated_contracts():
    # Get current logged-in user
    current_username = app.storage.user.get('username', None)
    current_user_id = None
    
    # Fetch current user from database
    try:
        db = SessionLocal()
        try:
            if current_username:
                # Try multiple matching strategies
                current_user = db.query(User).filter(User.email == current_username).first()
                if not current_user:
                    current_user = db.query(User).filter(User.email.ilike(f"%{current_username}%")).first()
                if not current_user:
                    current_user = db.query(User).filter(User.first_name.ilike(f"%{current_username}%")).first()
                if not current_user:
                    current_user = db.query(User).filter(User.last_name.ilike(f"%{current_username}%")).first()
                if not current_user and ' ' in current_username:
                    parts = current_username.split()
                    if len(parts) >= 2:
                        current_user = db.query(User).filter(
                            User.first_name.ilike(f"%{parts[0]}%"),
                            User.last_name.ilike(f"%{parts[-1]}%")
                        ).first()
                
                if current_user:
                    current_user_id = current_user.id
                    print(f"Found current user: {current_user.first_name} {current_user.last_name} (ID: {current_user_id})")
                else:
                    print(f"Could not find user matching: {current_username}")
                    default_user = db.query(User).first()
                    if default_user:
                        current_user_id = default_user.id
                        print(f"Using default user for simulation: {default_user.first_name} {default_user.last_name} (ID: {current_user_id})")
        finally:
            db.close()
    except Exception as e:
        print(f"Error fetching current user: {e}")
        import traceback
        traceback.print_exc()
    # Navigation
    with ui.row().classes("max-w-6xl mx-auto mt-4"):
        with ui.link(target='/').classes('no-underline'):
            ui.button("Back to Dashboard", icon="arrow_back").props('flat color=primary')
    
    # Global variables for table and data
    contracts_table = None
    contract_rows = []

    # Fetch terminated contracts from backend
    def fetch_terminated_contracts():
        """Load contracts with status Terminated from the database."""
        db = SessionLocal()
        try:
            contract_service = ContractService(db)
            contracts, _ = contract_service.get_terminated_contracts(skip=0, limit=1000)
            rows = []
            for contract in contracts:
                vendor_name = contract.vendor.vendor_name if contract.vendor else "Unknown"
                vendor_id = contract.vendor.id if contract.vendor else None
                contract_type = contract.contract_type.value if hasattr(contract.contract_type, "value") else str(contract.contract_type)
                department = contract.department.value if hasattr(contract.department, "value") else str(contract.department or "")
                exp_date = contract.end_date
                start_date = contract.start_date
                end_date = contract.end_date
                # Use last_modified_date as date_terminated when available, else end_date
                date_terminated = contract.last_modified_date.date() if getattr(contract, "last_modified_date", None) and hasattr(contract.last_modified_date, "date") else end_date
                if date_terminated is None:
                    date_terminated = end_date

                my_role = "N/A"
                if current_user_id:
                    if contract.contract_owner_id == current_user_id:
                        my_role = "Contract Manager"
                    elif contract.contract_owner_backup_id == current_user_id:
                        my_role = "Backup"
                    elif getattr(contract, "contract_owner_manager_id", None) and contract.contract_owner_manager_id == current_user_id:
                        my_role = "Owner"

                backup_name = ""
                if contract.contract_owner_backup:
                    backup_name = f"{contract.contract_owner_backup.first_name} {contract.contract_owner_backup.last_name}"

                rows.append({
                    "id": int(contract.id),
                    "contract_id": str(contract.contract_id or ""),
                    "vendor_id": int(vendor_id) if vendor_id else None,
                    "vendor_name": str(vendor_name or ""),
                    "contract_type": str(contract_type or ""),
                    "description": str(contract.contract_description or ""),
                    "start_date": start_date.strftime("%Y-%m-%d") if start_date else "",
                    "end_date": end_date.strftime("%Y-%m-%d") if end_date else "",
                    "expiration_date": exp_date.strftime("%Y-%m-%d") if exp_date else "",
                    "expiration_timestamp": datetime.combine(exp_date, datetime.min.time()).timestamp() if exp_date else 0,
                    "date_terminated": date_terminated.strftime("%Y-%m-%d") if date_terminated else "",
                    "date_terminated_timestamp": datetime.combine(date_terminated, datetime.min.time()).timestamp() if date_terminated else 0,
                    "status": "Terminated",
                    "my_role": str(my_role),
                    "backup": backup_name,
                    "department": str(department or ""),
                })
            return rows
        except Exception as e:
            print(f"Error fetching terminated contracts: {e}")
            import traceback
            traceback.print_exc()
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

    contract_rows = fetch_terminated_contracts()
    
    # Main container
    with ui.element("div").classes("max-w-6xl mt-8 mx-auto w-full"):
        # Section header
        with ui.row().classes('items-center justify-between ml-4 mb-4 w-full'):
            with ui.row().classes('items-center gap-2'):
                ui.icon('cancel', color='grey').style('font-size: 32px')
                ui.label("Terminated Contracts").classes("text-h5 font-bold")
        
        # Description row
        with ui.row().classes('ml-4 mb-4 w-full'):
            ui.label("Contracts that have been terminated").classes(
                "text-sm text-gray-500"
            )
        
        # Define search functions first
        def filter_contracts():
            # Show all contracts regardless of role
            base_rows = contract_rows
            
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
                    or search_term in (row['my_role'] or "").lower()
                ]
                contracts_table.rows = filtered
            contracts_table.update()
        
        def clear_search():
            search_input.value = ""
            filter_contracts()  # Use filter_contracts to respect current role
        
        # Search input for filtering contracts (above the table)
        with ui.row().classes('w-full ml-4 mr-4 mb-6 gap-2 px-2'):
            search_input = ui.input(placeholder='Search by Contract ID, Vendor, Type, Description, or My Role...').classes(
                'flex-1'
            ).props('outlined dense clearable')
            with search_input.add_slot('prepend'):
                ui.icon('search').classes('text-gray-400')
            ui.button(icon='search', on_click=filter_contracts).props('color=primary')
            ui.button(icon='clear', on_click=clear_search).props('color=secondary')
        
        # Create table after search bar (showing all contracts)
        initial_rows = contract_rows
        contracts_table = ui.table(
            columns=contract_columns,
            column_defaults=contract_columns_defaults,
            rows=initial_rows,
            pagination=10,
            row_key="id"
        ).classes("w-full").props("flat bordered").classes(
            "contracts-table shadow-lg rounded-lg overflow-hidden"
        )
        
        search_input.on_value_change(filter_contracts)
        
        # Generate button (moved from header to after table)
        ui.button("Generate", icon="description", on_click=lambda: open_generate_dialog()).props('color=primary').classes('ml-4 mt-4')
        
        # Add custom CSS for visual highlighting and toggle styling
        ui.add_css("""
            .contracts-table thead tr {
                background-color: #144c8e !important;
            }
            .contracts-table tbody tr {
                background-color: white !important;
            }
        """)
        
        # Add slot for contract ID with clickable link (links to contract info)
        contracts_table.add_slot('body-cell-contract_id', '''
            <q-td :props="props">
                <a :href="'/contract-info/' + props.row.id" class="text-blue-600 hover:text-blue-800 underline cursor-pointer">
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
        
        # Add slot for status column with normal text
        contracts_table.add_slot('body-cell-status', '''
            <q-td :props="props">
                <div class="text-gray-700">
                    {{ props.value }}
                </div>
            </q-td>
        ''')
        
        # Add slot for My Role column with badge styling
        contracts_table.add_slot('body-cell-my_role', '''
            <q-td :props="props">
                <q-badge 
                    v-if="props.value && props.value !== 'N/A'"
                    :color="props.value === 'Owner' ? 'primary' : (props.value === 'Contract Manager' ? 'blue' : 'orange')" 
                    :label="props.value"
                />
                <span v-else class="text-gray-500">{{ props.value || 'N/A' }}</span>
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
                        "My Role": contract.get('my_role', ''),
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
