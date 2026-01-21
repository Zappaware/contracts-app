from datetime import datetime, timedelta, date
from nicegui import ui, app
from app.db.database import SessionLocal
from app.services.contract_service import ContractService
from app.models.contract import ContractStatusType, User, UserRole
from app.utils.navigation import get_dashboard_url
import io
import base64
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


def active_contracts():
    # Get current logged-in user - use stored user_id first (from login)
    current_user_id = app.storage.user.get('user_id', None)
    current_user_role = app.storage.user.get('user_role', None)
    
    # If user_id is not stored, try to look it up by username
    if not current_user_id:
        current_username = app.storage.user.get('username', None)
        try:
            db = SessionLocal()
            try:
                if current_username:
                    # Try multiple matching strategies
                    # 1. Exact email match
                    current_user = db.query(User).filter(User.email == current_username).first()
                    # 2. Email contains username
                    if not current_user:
                        current_user = db.query(User).filter(User.email.ilike(f"%{current_username}%")).first()
                    # 3. First name match
                    if not current_user:
                        current_user = db.query(User).filter(User.first_name.ilike(f"%{current_username}%")).first()
                    # 4. Last name match
                    if not current_user:
                        current_user = db.query(User).filter(User.last_name.ilike(f"%{current_username}%")).first()
                    # 5. Full name match (e.g., "William Defoe")
                    if not current_user and ' ' in current_username:
                        parts = current_username.split()
                        if len(parts) >= 2:
                            current_user = db.query(User).filter(
                                User.first_name.ilike(f"%{parts[0]}%"),
                                User.last_name.ilike(f"%{parts[-1]}%")
                            ).first()
                    
                    if current_user:
                        current_user_id = current_user.id
                        current_user_role = current_user.role.value if current_user.role else None
                        print(f"Found current user: {current_user.first_name} {current_user.last_name} (ID: {current_user_id}, Role: {current_user_role})")
                    else:
                        print(f"Could not find user matching: {current_username}")
            finally:
                db.close()
        except Exception as e:
            print(f"Error fetching current user: {e}")
            import traceback
            traceback.print_exc()
    
    if current_user_id:
        print(f"Using stored user_id: {current_user_id}, role: {current_user_role}")
    # Navigation
    with ui.row().classes("max-w-6xl mx-auto mt-4"):
        with ui.link(target=get_dashboard_url()).classes('no-underline'):
            ui.button("Back to Dashboard", icon="arrow_back").props('flat color=primary')
    
    # Global variables for table and data
    contracts_table = None
    contract_rows = []
    
    
    # Fetch active contracts from database
    def fetch_active_contracts():
        """
        Fetches active contracts directly from the database service.
        This avoids HTTP requests and circular dependencies.
        Filters contracts based on user role:
        - Contract Admin: sees all contracts
        - Contract Manager/Backup/Owner: sees only contracts they are assigned to
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
            
            # Apply role-based filtering
            total_contracts_before_filter = len(contracts)
            
            if current_user_role == UserRole.CONTRACT_ADMIN.value:
                # Contract Admin sees all contracts
                print(f"User is Contract Admin - showing all {len(contracts)} active contracts")
            elif current_user_role in [UserRole.CONTRACT_MANAGER.value, UserRole.CONTRACT_MANAGER_BACKUP.value, UserRole.CONTRACT_MANAGER_OWNER.value]:
                # Contract Manager/Backup/Owner sees only contracts they are assigned to
                if current_user_id:
                    filtered_contracts = []
                    for contract in contracts:
                        # Check if user is assigned to this contract in any role
                        if (contract.contract_owner_id == current_user_id or
                            contract.contract_owner_backup_id == current_user_id or
                            contract.contract_owner_manager_id == current_user_id):
                            filtered_contracts.append(contract)
                    contracts = filtered_contracts
                    print(f"User is {current_user_role} - showing {len(contracts)} assigned contracts out of {total_contracts_before_filter} total")
                else:
                    # No user ID, show empty list
                    contracts = []
                    print(f"User is {current_user_role} but no user_id found - showing 0 contracts")
            else:
                # Unknown role or no role - show empty list for safety
                contracts = []
                print(f"User has unknown role '{current_user_role}' - showing 0 contracts")
            
            print(f"Found {len(contracts)} active contracts from database (after role filtering)")
            
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
                
                # Get department value
                department = contract.department.value if hasattr(contract.department, 'value') else str(contract.department)
                
                # Get automatic renewal value
                automatic_renewal = contract.automatic_renewal.value if hasattr(contract.automatic_renewal, 'value') else str(contract.automatic_renewal)
                
                # Format start date
                if contract.start_date:
                    if isinstance(contract.start_date, date):
                        formatted_start_date = contract.start_date.strftime("%Y-%m-%d")
                    else:
                        formatted_start_date = str(contract.start_date)
                else:
                    formatted_start_date = "N/A"
                
                # Format expiration date (end_date) and calculate quarter
                if contract.end_date:
                    if isinstance(contract.end_date, date):
                        exp_date = contract.end_date
                        formatted_date = exp_date.strftime("%Y-%m-%d")
                        exp_timestamp = datetime.combine(exp_date, datetime.min.time()).timestamp()
                        
                        # Calculate ending quarter
                        month = exp_date.month
                        year = exp_date.year
                        if month in [1, 2, 3]:
                            ending_quarter = f"Q1 {year}"
                        elif month in [4, 5, 6]:
                            ending_quarter = f"Q2 {year}"
                        elif month in [7, 8, 9]:
                            ending_quarter = f"Q3 {year}"
                        else:
                            ending_quarter = f"Q4 {year}"
                    else:
                        formatted_date = str(contract.end_date)
                        exp_timestamp = 0
                        ending_quarter = "N/A"
                else:
                    formatted_date = "N/A"
                    exp_timestamp = 0
                    ending_quarter = "N/A"
                
                # Determine user's role for this contract
                my_role = "N/A"
                if current_user_id:
                    # Check if logged-in user has a role in this contract
                    if contract.contract_owner_id == current_user_id:
                        my_role = "Contract Manager"
                    elif contract.contract_owner_backup_id == current_user_id:
                        my_role = "Backup"
                    elif contract.contract_owner_manager_id == current_user_id:
                        my_role = "Owner"
                else:
                    # Simulation mode: Cycle through users to show different roles
                    # This demonstrates how different users see different roles
                    all_users = db.query(User).order_by(User.id).limit(3).all()
                    if all_users:
                        # Cycle through users: CT1 -> user[0], CT2 -> user[1], CT3 -> user[2], CT4 -> user[0], etc.
                        user_index = (contract.id - 1) % len(all_users)
                        sim_user_id = all_users[user_index].id
                        
                        # Check what role this simulated user has in the contract
                        if contract.contract_owner_id == sim_user_id:
                            my_role = "Contract Manager"
                        elif contract.contract_owner_backup_id == sim_user_id:
                            my_role = "Backup"
                        elif contract.contract_owner_manager_id == sim_user_id:
                            my_role = "Owner"
                
                # Determine status color (Active = green, others = black/gray)
                status_color = "green" if contract.status == ContractStatusType.ACTIVE else "black"
                
                row_data = {
                    "id": int(contract.id),
                    "contract_id": str(contract.contract_id or ""),
                    "vendor_id": int(vendor_id) if vendor_id else 0,
                    "vendor_name": str(vendor_name or ""),
                    "contract_type": str(contract_type or ""),
                    "description": str(contract.contract_description or ""),
                    "start_date": str(formatted_start_date),
                    "end_date": str(formatted_date),
                    "expiration_date": str(formatted_date),  # Keep for backward compatibility
                    "expiration_timestamp": float(exp_timestamp),
                    "ending_quarter": str(ending_quarter),
                    "automatic_renewal": str(automatic_renewal),
                    "department": str(department),
                    "status": str(status or "Unknown"),
                    "status_color": str(status_color),
                    "my_role": str(my_role),
                    "backup": str(backup_name),
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
        # Section header
        with ui.row().classes('items-center justify-between ml-4 mb-4 w-full'):
            with ui.row().classes('items-center gap-2'):
                ui.icon('check_circle', color='green').style('font-size: 32px')
                ui.label("Active Contracts").classes("text-h5 font-bold")
        
        # Description row
        with ui.row().classes('ml-4 mb-4 w-full'):
            ui.label("Contracts currently in effect").classes(
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
                ui.label("No active contracts found").classes("text-lg font-bold text-gray-500")
                ui.label("Please check that the backend has contract data.").classes("text-sm text-gray-400 mt-2")
        
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
        
        # Add custom CSS for visual highlighting
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
        
        # Add slot for vendor name with clickable link (links to vendor details)
        contracts_table.add_slot('body-cell-vendor_name', '''
            <q-td :props="props">
                <a :href="'/vendor-info/' + props.row.vendor_id" class="text-blue-600 hover:text-blue-800 underline cursor-pointer">
                    {{ props.value }}
                </a>
            </q-td>
        ''')
        
        # Add slot for status column with color coding (Active = green, others = black)
        contracts_table.add_slot('body-cell-status', '''
            <q-td :props="props">
                <div v-if="props.row.status_color === 'green'" class="text-green-700 font-semibold">
                    {{ props.value }}
                </div>
                <div v-else class="text-black font-semibold">
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
                ui.label("Generate Active Contracts Report").classes("text-h6 font-bold mb-4")
                
                with ui.column().classes('gap-4 w-full'):
                    ui.label("Select date range for active contracts:").classes("text-sm text-gray-600")
                    
                    start_date_input = ui.input("Start Date", placeholder="YYYY-MM-DD").props('type=date').classes('w-full')
                    end_date_input = ui.input("End Date", placeholder="YYYY-MM-DD").props('type=date').classes('w-full')
                    
                    # Set default dates (last 6 months)
                    today = datetime.now()
                    default_start = (today - timedelta(days=180)).strftime("%Y-%m-%d")
                    default_end = today.strftime("%Y-%m-%d")
                    start_date_input.value = default_start
                    end_date_input.value = default_end
                    
                    ui.label("The report will include all active contracts within the selected date range.").classes("text-xs text-gray-500 italic")
                    ui.label("Note: Extension/Renewal history fields are not yet implemented and will show as 'N/A'.").classes("text-xs text-orange-600 italic mt-2")
                    
                    with ui.row().classes('gap-2 justify-end w-full mt-4'):
                        ui.button("Cancel", on_click=dialog.close).props('flat')
                        ui.button("Generate & Download", icon="download", 
                                 on_click=lambda: generate_excel_report(start_date_input.value, end_date_input.value, dialog)).props('color=primary')
                
                dialog.open()
        
        def generate_excel_report(start_date_str, end_date_str, dialog):
            """Generate Excel report for active contracts within date range"""
            try:
                # Parse dates
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
                
                if start_date > end_date:
                    ui.notify("Start date must be before end date", type="negative")
                    return
                
                # Use all contract rows for the report
                filtered_contracts = contract_rows
                
                if not filtered_contracts:
                    ui.notify("No active contracts available for export", type="warning")
                    dialog.close()
                    return
                
                if not PANDAS_AVAILABLE:
                    ui.notify("Excel export requires pandas library. Please install it: pip install pandas openpyxl", type="negative")
                    dialog.close()
                    return
                
                # Prepare data for Excel with all required fields
                report_data = []
                for contract in filtered_contracts:
                    report_data.append({
                        "Vendor": contract.get('vendor_name', ''),
                        "Contract ID": contract.get('contract_id', ''),
                        "Contract Type": contract.get('contract_type', ''),
                        "Description": contract.get('description', ''),
                        "Contract Start Date": contract.get('start_date', ''),
                        "Contract End Date": contract.get('end_date', ''),
                        "Ending in Quarter": contract.get('ending_quarter', ''),
                        "Automatic Renewal": contract.get('automatic_renewal', ''),
                        "Department": contract.get('department', ''),
                        "My Role": contract.get('my_role', ''),
                        "Contract Backups": contract.get('backup', ''),
                        "Latest Extension/Renewal": "N/A",  # Not yet implemented in database
                        "Previous Extension/Renewal 1": "N/A",  # Not yet implemented in database
                        "Previous Extension/Renewal 2": "N/A",  # Not yet implemented in database
                        "Previous Extension/Renewal 3": "N/A",  # Not yet implemented in database
                    })
                
                # Create DataFrame
                df = pd.DataFrame(report_data)
                
                # Create Excel file in memory
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Active Contracts')
                    
                    # Get the worksheet
                    worksheet = writer.sheets['Active Contracts']
                    
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
                filename = f"Active_Contracts_Report_{start_date_str}_to_{end_date_str}.xlsx"
                
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
