from nicegui import ui
import io
import base64
from datetime import datetime
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


def contract_managers():
    # Navigation
    with ui.row().classes("max-w-6xl mx-auto mt-4"):
        with ui.link(target='/').classes('no-underline'):
            ui.button("Back to Dashboard", icon="arrow_back").props('flat color=primary')
    
    # Global variables for table and data
    managers_table = None
    manager_rows = []
    
    # Fetch users with their active contract counts by role
    def fetch_users_with_contract_counts():
        """
        Fetches all users from the database and counts their active contracts
        in each role: Contract Manager, Backup, and Owner.
        """
        try:
            from app.db.database import SessionLocal
            from app.models.contract import User, Contract, ContractStatusType
            
            db = SessionLocal()
            try:
                # Get all active users
                users = db.query(User).filter(User.is_active == True).all()
                
                if not users:
                    print("No users found in database")
                    return []
                
                rows = []
                for user in users:
                    # Count active contracts where user is Contract Manager (contract_owner_id)
                    contract_manager_count = db.query(Contract).filter(
                        Contract.contract_owner_id == user.id,
                        Contract.status == ContractStatusType.ACTIVE
                    ).count()
                    
                    # Count active contracts where user is Backup (contract_owner_backup_id)
                    backup_count = db.query(Contract).filter(
                        Contract.contract_owner_backup_id == user.id,
                        Contract.status == ContractStatusType.ACTIVE
                    ).count()
                    
                    # Count active contracts where user is Owner (contract_owner_manager_id)
                    owner_count = db.query(Contract).filter(
                        Contract.contract_owner_manager_id == user.id,
                        Contract.status == ContractStatusType.ACTIVE
                    ).count()
                    
                    # Get department value
                    department = user.department.value if hasattr(user.department, 'value') else str(user.department)
                    
                    row_data = {
                        "user_id": str(user.user_id or ""),
                        "name": f"{user.first_name} {user.last_name}",
                        "email": str(user.email or ""),
                        "department": str(department or ""),
                        "contract_manager_count": int(contract_manager_count),
                        "backup_count": int(backup_count),
                        "owner_count": int(owner_count),
                    }
                    rows.append(row_data)
                
                print(f"Processed {len(rows)} user rows")
                return rows
                
            finally:
                db.close()
        except Exception as e:
            error_msg = f"Error fetching users: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            ui.notify(error_msg, type="negative")
            return []

    manager_columns = [
        {
            "name": "user_id",
            "label": "User ID",
            "field": "user_id",
            "align": "left",
            "sortable": True,
        },
        {
            "name": "name",
            "label": "Name",
            "field": "name",
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
            "name": "department",
            "label": "Department",
            "field": "department",
            "align": "left",
            "sortable": True,
        },
        {
            "name": "contract_manager_count",
            "label": "Contract Manager",
            "field": "contract_manager_count",
            "align": "center",
            "sortable": True,
        },
        {
            "name": "backup_count",
            "label": "Backup",
            "field": "backup_count",
            "align": "center",
            "sortable": True,
        },
        {
            "name": "owner_count",
            "label": "Owner",
            "field": "owner_count",
            "align": "center",
            "sortable": True,
        },
    ]

    manager_columns_defaults = {
        "align": "left",
        "headerClasses": "bg-[#144c8e] text-white",
    }

    manager_rows = fetch_users_with_contract_counts()
    
    # Main container
    with ui.element("div").classes("max-w-6xl mt-8 mx-auto w-full"):
        # Section header
        with ui.row().classes('items-center ml-4 mb-4 w-full'):
            with ui.row().classes('items-center gap-2'):
                ui.icon('people', color='primary').style('font-size: 32px')
                ui.label("User Administration").classes("text-h5 font-bold")
        
        ui.label("View user responsibilities based on their assigned roles").classes(
            "text-sm text-gray-500 ml-4 mb-4"
        )
        
        # Define search functions first
        def filter_managers():
            search_term = (search_input.value or "").lower()
            if not search_term:
                managers_table.rows = manager_rows
            else:
                filtered = [
                    row for row in manager_rows
                    if search_term in (row['user_id'] or "").lower()
                    or search_term in (row['name'] or "").lower()
                    or search_term in (row['email'] or "").lower()
                    or search_term in (row['department'] or "").lower()
                    or search_term in str(row.get('contract_manager_count', '')).lower()
                    or search_term in str(row.get('backup_count', '')).lower()
                    or search_term in str(row.get('owner_count', '')).lower()
                ]
                managers_table.rows = filtered
            managers_table.update()
        
        def clear_search():
            search_input.value = ""
            managers_table.rows = manager_rows
            managers_table.update()
        
        # Search input for filtering managers (above the table)
        with ui.row().classes('w-full ml-4 mr-4 mb-6 gap-2 px-2'):
            search_input = ui.input(placeholder='Search by ID, Name, Email, Department, or Contract Counts...').classes(
                'flex-1'
            ).props('outlined dense clearable')
            with search_input.add_slot('prepend'):
                ui.icon('search').classes('text-gray-400')
            search_button = ui.button(icon='search', on_click=filter_managers).props('color=primary')
            clear_button = ui.button(icon='clear', on_click=clear_search).props('color=secondary')
        
        # Create table after search bar
        managers_table = ui.table(
            columns=manager_columns,
            column_defaults=manager_columns_defaults,
            rows=manager_rows,
            pagination=10,
            row_key="user_id"
        ).classes("w-full").props("flat bordered").classes(
            "managers-table shadow-lg rounded-lg overflow-hidden"
        )
        
        search_input.on_value_change(filter_managers)
        
        # Generate button (moved from header to after table)
        ui.button("Generate", icon="description", on_click=lambda: open_generate_dialog()).props('color=primary').classes('ml-4 mt-4')
        
        # Add custom CSS for visual highlighting
        ui.add_css("""
            .managers-table thead tr {
                background-color: #144c8e !important;
            }
            .managers-table tbody tr {
                background-color: white !important;
            }
        """)
        
        # Add slot for contract manager count with centered badge
        managers_table.add_slot('body-cell-contract_manager_count', '''
            <q-td :props="props" class="text-center">
                <q-badge 
                    color="grey-6" 
                    :label="props.value"
                />
            </q-td>
        ''')
        
        # Add slot for backup count with centered badge
        managers_table.add_slot('body-cell-backup_count', '''
            <q-td :props="props" class="text-center">
                <q-badge 
                    color="grey-6" 
                    :label="props.value"
                />
            </q-td>
        ''')
        
        # Add slot for owner count with centered badge
        managers_table.add_slot('body-cell-owner_count', '''
            <q-td :props="props" class="text-center">
                <q-badge 
                    color="grey-6" 
                    :label="props.value"
                />
            </q-td>
        ''')
        
        # Add slot for email with mailto link
        managers_table.add_slot('body-cell-email', '''
            <q-td :props="props">
                <a :href="'mailto:' + props.value" class="text-blue-600 hover:text-blue-800 underline">
                    {{ props.value }}
                </a>
            </q-td>
        ''')
        
        # Function to generate Excel report
        def open_generate_dialog():
            """Open dialog for report generation"""
            with ui.dialog() as dialog, ui.card().classes('p-6 w-full max-w-md'):
                ui.label("Generate User Administration Report").classes("text-h6 font-bold mb-4")
                
                with ui.column().classes('gap-4 w-full'):
                    ui.label("This report will include all users with their contract responsibilities.").classes("text-sm text-gray-600")
                    
                    ui.label("The report will include: User ID, Name, Email, Department, Contract Manager count, Backup count, and Owner count.").classes("text-xs text-gray-500 italic")
                    
                    with ui.row().classes('gap-2 justify-end w-full mt-4'):
                        ui.button("Cancel", on_click=dialog.close).props('flat')
                        ui.button("Generate & Download", icon="download", 
                                 on_click=lambda: generate_excel_report(dialog)).props('color=primary')
                
                dialog.open()
        
        def generate_excel_report(dialog):
            """Generate Excel report for user administration"""
            try:
                if not PANDAS_AVAILABLE:
                    ui.notify("Excel export requires pandas library. Please install it: pip install pandas openpyxl", type="negative")
                    dialog.close()
                    return
                
                if not manager_rows:
                    ui.notify("No users available for export", type="warning")
                    dialog.close()
                    return
                
                # Prepare data for Excel
                report_data = []
                for user in manager_rows:
                    report_data.append({
                        "User ID": user.get('user_id', ''),
                        "Name": user.get('name', ''),
                        "Email": user.get('email', ''),
                        "Department": user.get('department', ''),
                        "Contract Manager": user.get('contract_manager_count', 0),
                        "Backup": user.get('backup_count', 0),
                        "Owner": user.get('owner_count', 0),
                    })
                
                # Create DataFrame
                df = pd.DataFrame(report_data)
                
                # Create Excel file in memory
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='User Administration')
                    
                    # Get the worksheet
                    worksheet = writer.sheets['User Administration']
                    
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
                today = datetime.now().strftime("%Y-%m-%d")
                filename = f"User_Administration_Report_{today}.xlsx"
                
                # Trigger download using JavaScript
                ui.run_javascript(f'''
                    const link = document.createElement('a');
                    link.href = 'data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64_data}';
                    link.download = '{filename}';
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                ''')
                
                ui.notify(f"Report generated successfully! {len(manager_rows)} user(s) exported.", type="positive")
                dialog.close()
                
            except Exception as e:
                ui.notify(f"Error generating report: {str(e)}", type="negative")
                import traceback
                traceback.print_exc()
