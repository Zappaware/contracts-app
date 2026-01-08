from datetime import datetime, timedelta, date
from nicegui import ui
from app.db.database import SessionLocal
from app.services.contract_service import ContractService
from app.models.contract import ContractStatusType
import io
import base64
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


def expired_contracts():
    # Navigation
    with ui.row().classes("max-w-6xl mx-auto mt-4"):
        with ui.link(target='/').classes('no-underline'):
            ui.button("Back to Dashboard", icon="arrow_back").props('flat color=primary')
    
    # Global variables for table and data
    contracts_table = None
    contract_rows = []
    
    
    # Fetch expired contracts from database
    def fetch_expired_contracts():
        """
        Fetches expired contracts directly from the database service.
        This avoids HTTP requests and circular dependencies.
        """
        db = SessionLocal()
        try:
            contract_service = ContractService(db)
            
            # Get expired contracts only (limit 1000 for display)
            contracts, _ = contract_service.search_and_filter_contracts(
                skip=0,
                limit=1000,
                status=ContractStatusType.EXPIRED,
                search=None,
                contract_type=None,
                department=None,
                owner_id=None,
                vendor_id=None,
                expiring_soon=None
            )
            
            print(f"Found {len(contracts)} expired contracts from database")
            
            if not contracts:
                print("No expired contracts found in database")
                return []
            
            # Map contract data to table row format
            rows = []
            for contract in contracts:
                # Get contract owner (manager) name
                manager_name = f"{contract.contract_owner.first_name} {contract.contract_owner.last_name}"
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
                
                # Format start date
                if contract.start_date:
                    if isinstance(contract.start_date, date):
                        formatted_start_date = contract.start_date.strftime("%Y-%m-%d")
                    else:
                        formatted_start_date = str(contract.start_date)
                else:
                    formatted_start_date = "N/A"
                
                # Calculate days past due (difference between today and end_date)
                days_past_due = 0
                if contract.end_date and isinstance(contract.end_date, date):
                    today = date.today()
                    if contract.end_date < today:
                        days_past_due = (today - contract.end_date).days
                
                # Count email notifications for this contract
                # Note: ContractNotification table may not exist or may reference a different schema
                # Try to query using raw SQL to avoid importing the model (which has duplicate User class)
                email_notification_count = 0
                try:
                    # Query using raw SQL to avoid model import conflicts
                    from sqlalchemy import text
                    result = db.execute(
                        text("SELECT COUNT(*) FROM contract_notifications WHERE contract_id = :contract_id"),
                        {"contract_id": contract.id}
                    ).scalar()
                    email_notification_count = result if result else 0
                except Exception:
                    # If table doesn't exist or query fails, default to 0
                    # This is expected if the notification system isn't set up
                    pass
                
                rows.append({
                    "id": contract.id,  # Internal ID for routing
                    "contract_id": contract.contract_id,
                    "vendor_name": vendor_name,
                    "vendor_id": vendor_id,
                    "contract_type": contract_type,
                    "description": contract.contract_description,
                    "start_date": formatted_start_date,
                    "expiration_date": formatted_date,
                    "expiration_timestamp": exp_timestamp,
                    "status": status,
                    "department": department,
                    "manager": manager_name,
                    "backup": backup_name,
                    "days_past_due": days_past_due,
                    "email_notifications": email_notification_count,
                })
            
            return rows
            
        except Exception as e:
            print(f"Error fetching expired contracts: {str(e)}")
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

    contract_rows = fetch_expired_contracts()
    
    # Main container
    with ui.element("div").classes("max-w-6xl mt-8 mx-auto w-full"):
        # Section header with toggle and Generate button
        with ui.row().classes('items-center justify-between ml-4 mb-4 w-full'):
            with ui.row().classes('items-center gap-2'):
                ui.icon('warning', color='red').style('font-size: 32px')
                ui.label("Expired Contracts").classes("text-h5 font-bold")
            
            with ui.row().classes('items-center gap-3'):
                # Generate Report button
                ui.button("Generate", icon="description", on_click=lambda: open_generate_dialog()).props('color=primary')
        
        # Description row
        with ui.row().classes('ml-4 mb-4 w-full'):
            ui.label("Contracts that have passed their expiration date").classes(
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
        
        # Create table after search bar (showing all contracts)
        initial_rows = contract_rows
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
        
        # Function to generate Excel report
        def open_generate_dialog():
            """Open dialog for date range selection and report generation"""
            with ui.dialog() as dialog, ui.card().classes('p-6 w-full max-w-md'):
                ui.label("Generate Expired Contracts Report").classes("text-h6 font-bold mb-4")
                
                with ui.column().classes('gap-4 w-full'):
                    ui.label("Select date range for expired contracts:").classes("text-sm text-gray-600")
                    
                    start_date_input = ui.input("Start Date", placeholder="YYYY-MM-DD").props('type=date').classes('w-full')
                    end_date_input = ui.input("End Date", placeholder="YYYY-MM-DD").props('type=date').classes('w-full')
                    
                    # Set default dates (last 6 months)
                    today = datetime.now()
                    default_start = (today - timedelta(days=180)).strftime("%Y-%m-%d")
                    default_end = today.strftime("%Y-%m-%d")
                    start_date_input.value = default_start
                    end_date_input.value = default_end
                    
                    ui.label("The report will include all expired contracts within the selected date range.").classes("text-xs text-gray-500 italic")
                    
                    with ui.row().classes('gap-2 justify-end w-full mt-4'):
                        ui.button("Cancel", on_click=dialog.close).props('flat')
                        ui.button("Generate & Download", icon="download", 
                                 on_click=lambda: generate_excel_report(start_date_input.value, end_date_input.value, dialog)).props('color=primary')
                
                dialog.open()
        
        def generate_excel_report(start_date_str, end_date_str, dialog):
            """Generate Excel report for expired contracts within date range"""
            try:
                if not PANDAS_AVAILABLE:
                    ui.notify("Excel export requires pandas library. Please install it: pip install pandas openpyxl", type="negative")
                    dialog.close()
                    return
                
                # Parse dates
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                
                if start_date > end_date:
                    ui.notify("Start date must be before end date", type="negative")
                    return
                
                # Filter contracts by date range (end_date must be within range) and status must be Expired
                filtered_contracts = []
                for contract in contract_rows:
                    # Check if contract has expiration date within range
                    exp_date_str = contract.get('expiration_date', '')
                    if exp_date_str and exp_date_str != 'N/A':
                        try:
                            exp_date = datetime.strptime(exp_date_str, "%Y-%m-%d").date()
                            # Include contracts that expired within the date range
                            if start_date <= exp_date <= end_date and contract.get('status') == 'Expired':
                                filtered_contracts.append(contract)
                        except ValueError:
                            # Skip contracts with invalid date format
                            continue
                
                if not filtered_contracts:
                    ui.notify("No expired contracts found within the selected date range", type="warning")
                    dialog.close()
                    return
                
                # Prepare data for Excel with all required fields
                report_data = []
                for contract in filtered_contracts:
                    report_data.append({
                        "Contract ID": contract.get('contract_id', ''),
                        "Contract Type": contract.get('contract_type', ''),
                        "Description": contract.get('description', ''),
                        "Vendor": contract.get('vendor_name', ''),
                        "Contract Start": contract.get('start_date', ''),
                        "Contract End Date": contract.get('expiration_date', ''),
                        "Department": contract.get('department', ''),
                        "Contract Manager": contract.get('manager', ''),
                        "Contract Backups": contract.get('backup', ''),
                        "Days Past Due": contract.get('days_past_due', 0),
                        "Email Notifications": contract.get('email_notifications', 0),
                    })
                
                # Create DataFrame
                df = pd.DataFrame(report_data)
                
                # Create Excel file in memory
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Expired Contracts')
                    
                    # Get the worksheet
                    worksheet = writer.sheets['Expired Contracts']
                    
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
                filename = f"Expired_Contracts_Report_{start_date_str}_to_{end_date_str}.xlsx"
                
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
