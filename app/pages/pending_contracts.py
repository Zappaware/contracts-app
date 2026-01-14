from datetime import datetime, timedelta, date
from nicegui import ui, app
import io
import base64
from app.db.database import SessionLocal
from app.services.contract_service import ContractService
from app.models.contract import ContractStatusType, User
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


def pending_contracts():
    # Get current logged-in user - use stored user_id first (from login)
    current_user_id = app.storage.user.get('user_id', None)
    
    # If user_id is not stored, try to look it up by username
    if not current_user_id:
        current_username = app.storage.user.get('username', None)
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
            finally:
                db.close()
        except Exception as e:
            print(f"Error fetching current user: {e}")
            import traceback
            traceback.print_exc()
    
    if current_user_id:
        print(f"Using stored user_id: {current_user_id}")
    # Navigation
    with ui.row().classes("max-w-6xl mx-auto mt-4"):
        with ui.link(target='/').classes('no-underline'):
            ui.button("Back to Dashboard", icon="arrow_back").props('flat color=primary')
    
    # Global variables for table and data
    contracts_table = None
    contract_rows = []
    
    # Function to handle owned/backup toggle
    
    # Fetch contracts with no documents from database
    def fetch_pending_documents_contracts():
        """
        Fetches active contracts that have no documents uploaded.
        """
        db = SessionLocal()
        try:
            contract_service = ContractService(db)
            
            # Get contracts with no documents (limit 1000 for display)
            contracts, _ = contract_service.get_contracts_with_no_documents(
                skip=0,
                limit=1000
            )
            
            print(f"Found {len(contracts)} contracts with no documents from database")
            
            if not contracts:
                print("No contracts with pending documents found in database")
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
                
                # Determine user's role for this contract
                my_role = "N/A"
                if current_user_id:
                    if contract.contract_owner_id == current_user_id:
                        my_role = "Contract Manager"
                    elif contract.contract_owner_backup_id == current_user_id:
                        my_role = "Backup"
                    elif contract.contract_owner_manager_id == current_user_id:
                        my_role = "Owner"
                else:
                    # Simulation mode: Cycle through users to show different roles
                    all_users = db.query(User).order_by(User.id).limit(3).all()
                    if all_users:
                        user_index = (contract.id - 1) % len(all_users)
                        sim_user_id = all_users[user_index].id
                        if contract.contract_owner_id == sim_user_id:
                            my_role = "Contract Manager"
                        elif contract.contract_owner_backup_id == sim_user_id:
                            my_role = "Backup"
                        elif contract.contract_owner_manager_id == sim_user_id:
                            my_role = "Owner"
                
                row_data = {
                    "id": int(contract.id),
                    "contract_id": str(contract.contract_id or ""),
                    "vendor_id": int(vendor_id) if vendor_id else 0,
                    "vendor_name": str(vendor_name or ""),
                    "contract_type": str(contract_type or ""),
                    "description": str(contract.contract_description or ""),
                    "expiration_date": str(formatted_date),
                    "expiration_timestamp": float(exp_timestamp),
                    "status": "Pending documents",  # Display status (not from DB)
                    "my_role": str(my_role),
                }
                rows.append(row_data)
            
            print(f"Processed {len(rows)} contract rows")
            return rows
            
        except Exception as e:
            error_msg = f"Error fetching pending contracts: {str(e)}"
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

    contract_rows = []
    
    # Initial fetch
    contract_rows = fetch_pending_documents_contracts()
    
    # Debug: Check if we have data
    print(f"Total contract rows fetched: {len(contract_rows)}")
    if contract_rows:
        print(f"First row sample: {contract_rows[0]}")
    else:
        ui.notify("No pending documents contracts available. All active contracts have documents uploaded.", type="info")
    
    # Main container
    with ui.element("div").classes("max-w-6xl mt-8 mx-auto w-full"):
        # Section header
        with ui.row().classes('items-center justify-between ml-4 mb-4 w-full'):
            with ui.row().classes('items-center gap-2'):
                ui.icon('edit', color='orange').style('font-size: 32px')
                ui.label("Pending Documents").classes("text-h5 font-bold")
        
        # Description row
        with ui.row().classes('ml-4 mb-4 w-full'):
            ui.label("Contracts missing required documents").classes(
                "text-sm text-gray-500"
            )
        
        # Count label row
        with ui.row().classes('ml-4 mb-2'):
            count_label = ui.label(f"Total: {len(contract_rows)} contracts").classes("text-sm text-gray-500")
        
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
        
        # Show message if no data
        if not contract_rows:
            with ui.card().classes("w-full p-6"):
                ui.label("No pending documents contracts found").classes("text-lg font-bold text-gray-500")
                ui.label("All active contracts have documents uploaded, or there are no active contracts.").classes("text-sm text-gray-400 mt-2")
        
        # Create table after search bar (showing all contracts)
        initial_rows = contract_rows
        print(f"Creating table with {len(initial_rows)} rows")
        
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
        
        # Generate button (moved from header to after table)
        ui.button("Generate", icon="description", on_click=lambda: open_generate_dialog()).props('color=primary').classes('ml-4 mt-4')
        
        search_input.on_value_change(filter_contracts)
        
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
        
        # Add slot for custom styling of status column
        contracts_table.add_slot('body-cell-status', '''
            <q-td :props="props">
                <div class="text-orange-600 font-semibold flex items-center gap-1">
                    <q-icon name="pending" color="orange" size="sm" />
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
                ui.label("Generate Pending Documents Report").classes("text-h6 font-bold mb-4")
                
                with ui.column().classes('gap-4 w-full'):
                    ui.label("Select date range for pending documents:").classes("text-sm text-gray-600")
                    
                    start_date_input = ui.input("Start Date", placeholder="YYYY-MM-DD").props('type=date').classes('w-full')
                    end_date_input = ui.input("End Date", placeholder="YYYY-MM-DD").props('type=date').classes('w-full')
                    
                    # Set default dates (last 6 months)
                    today = datetime.now()
                    default_start = (today - timedelta(days=180)).strftime("%Y-%m-%d")
                    default_end = today.strftime("%Y-%m-%d")
                    start_date_input.value = default_start
                    end_date_input.value = default_end
                    
                    ui.label("The report will include all contracts with pending documents.").classes("text-xs text-gray-500 italic")
                    
                    with ui.row().classes('gap-2 justify-end w-full mt-4'):
                        ui.button("Cancel", on_click=dialog.close).props('flat')
                        ui.button("Generate & Download", icon="download", 
                                 on_click=lambda: generate_excel_report(start_date_input.value, end_date_input.value, dialog)).props('color=primary')
                
                dialog.open()
        
        def generate_excel_report(start_date_str, end_date_str, dialog):
            """Generate Excel report for pending contracts"""
            try:
                if not PANDAS_AVAILABLE:
                    ui.notify("Excel export requires pandas library. Please install it: pip install pandas openpyxl", type="negative")
                    dialog.close()
                    return
                
                if not contract_rows:
                    ui.notify("No pending contracts available for export", type="warning")
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
                        "My Role": contract.get('my_role', ''),
                    })
                
                # Create DataFrame
                df = pd.DataFrame(report_data)
                
                # Create Excel file in memory
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Pending Documents')
                    
                    # Get the worksheet
                    worksheet = writer.sheets['Pending Documents']
                    
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
                filename = f"Pending_Documents_Report_{start_date_str}_to_{end_date_str}.xlsx"
                
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
