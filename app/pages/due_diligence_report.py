from datetime import datetime, timedelta, date
from nicegui import ui
from app.db.database import SessionLocal
from app.models.vendor import VendorStatusType
import io
import base64
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


def due_diligence_report():
    # Navigation
    with ui.row().classes("max-w-6xl mx-auto mt-4"):
        with ui.link(target='/').classes('no-underline'):
            ui.button("Back to Dashboard", icon="arrow_back").props('flat color=primary')
    
    # Global variables for table and data
    vendors_table = None
    vendor_rows = []
    
    
    # Fetch active vendors with due diligence information
    def fetch_due_diligence_vendors():
        """
        Fetches active vendors with their due diligence information and associated contract managers/backups.
        """
        db = SessionLocal()
        try:
            # Get all active vendors (limit 1000 for display)
            # Need to load contracts relationship with owners
            from sqlalchemy.orm import joinedload
            from app.models.vendor import Vendor
            from app.models.contract import Contract
            
            query = db.query(Vendor).filter(Vendor.status == VendorStatusType.ACTIVE)
            query = query.options(joinedload(Vendor.contracts).joinedload(Contract.contract_owner))
            query = query.options(joinedload(Vendor.contracts).joinedload(Contract.contract_owner_backup))
            vendors = query.limit(1000).all()
            
            print(f"Found {len(vendors)} active vendors from database")
            
            if not vendors:
                print("No active vendors found in database")
                return []
            
            # Map vendor data to table row format
            rows = []
            for vendor in vendors:
                # Format last due diligence date
                if vendor.last_due_diligence_date:
                    if isinstance(vendor.last_due_diligence_date, datetime):
                        last_dd_date = vendor.last_due_diligence_date.date()
                        formatted_last_dd = last_dd_date.strftime("%Y-%m-%d")
                    else:
                        formatted_last_dd = vendor.last_due_diligence_date.strftime("%Y-%m-%d")
                else:
                    formatted_last_dd = "N/A"
                
                # Format next required due diligence date
                days_past_due = 0
                if vendor.next_required_due_diligence_date:
                    if isinstance(vendor.next_required_due_diligence_date, datetime):
                        next_dd_date = vendor.next_required_due_diligence_date.date()
                        formatted_next_dd = next_dd_date.strftime("%Y-%m-%d")
                        
                        # Calculate days past due
                        today = date.today()
                        if next_dd_date < today:
                            days_past_due = (today - next_dd_date).days
                    else:
                        formatted_next_dd = vendor.next_required_due_diligence_date.strftime("%Y-%m-%d")
                        today = date.today()
                        if vendor.next_required_due_diligence_date < today:
                            days_past_due = (today - vendor.next_required_due_diligence_date).days
                else:
                    formatted_next_dd = "N/A"
                
                # Get contract managers and backups from vendor's active contracts
                contract_managers = set()
                contract_backups = set()
                
                if vendor.contracts:
                    for contract in vendor.contracts:
                        # Only include active contracts
                        if contract.status and hasattr(contract.status, 'value'):
                            contract_status = contract.status.value if hasattr(contract.status, 'value') else str(contract.status)
                            if contract_status != "Active":
                                continue
                        elif str(contract.status) != "Active":
                            continue
                        
                        # Get contract manager (owner)
                        if contract.contract_owner:
                            manager_name = f"{contract.contract_owner.first_name} {contract.contract_owner.last_name}"
                            contract_managers.add(manager_name)
                        
                        # Get contract backup
                        if contract.contract_owner_backup:
                            backup_name = f"{contract.contract_owner_backup.first_name} {contract.contract_owner_backup.last_name}"
                            contract_backups.add(backup_name)
                
                # Convert sets to comma-separated strings
                managers_str = ", ".join(sorted(contract_managers)) if contract_managers else "N/A"
                backups_str = ", ".join(sorted(contract_backups)) if contract_backups else "N/A"
                
                rows.append({
                    "id": vendor.id,  # Internal ID for routing
                    "vendor_id": vendor.vendor_id,
                    "vendor_name": vendor.vendor_name,
                    "last_due_diligence_date": formatted_last_dd,
                    "next_required_due_diligence_date": formatted_next_dd,
                    "days_past_due": days_past_due,
                    "contract_manager": managers_str,
                    "contract_backups": backups_str,
                })
            
            return rows
            
        except Exception as e:
            print(f"Error fetching due diligence vendors: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            db.close()

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
            "label": "Vendor",
            "field": "vendor_name",
            "align": "left",
            "sortable": True,
        },
        {
            "name": "last_due_diligence_date",
            "label": "Last Due Diligence Date",
            "field": "last_due_diligence_date",
            "align": "left",
            "sortable": True,
        },
        {
            "name": "next_required_due_diligence_date",
            "label": "Next Required Due Diligence Date",
            "field": "next_required_due_diligence_date",
            "align": "left",
            "sortable": True,
        },
        {
            "name": "days_past_due",
            "label": "Days Past Due",
            "field": "days_past_due",
            "align": "right",
            "sortable": True,
        },
        {
            "name": "contract_manager",
            "label": "Contract Manager",
            "field": "contract_manager",
            "align": "left",
        },
        {
            "name": "contract_backups",
            "label": "Contract Backups",
            "field": "contract_backups",
            "align": "left",
        },
    ]

    vendor_columns_defaults = {
        "align": "left",
        "headerClasses": "bg-[#144c8e] text-white",
    }

    vendor_rows = fetch_due_diligence_vendors()
    
    # Main container
    with ui.element("div").classes("max-w-6xl mt-8 mx-auto w-full"):
        # Section header
        with ui.row().classes('items-center justify-between ml-4 mb-4 w-full'):
            with ui.row().classes('items-center gap-2'):
                ui.icon('assignment', color='orange').style('font-size: 32px')
                ui.label("Vendors Due Diligence Report").classes("text-h5 font-bold")
        
        # Description row
        with ui.row().classes('ml-4 mb-4 w-full'):
            ui.label("Active vendors with due diligence information and their contract managers").classes(
                "text-sm text-gray-500"
            )
        
        # Count label row
        with ui.row().classes('ml-4 mb-2'):
            count_label = ui.label(f"Total: {len(vendor_rows)} vendor(s)").classes("text-sm text-gray-500")
        
        # Define search functions first
        def filter_vendors():
            base_rows = vendor_rows
            
            search_term = (search_input.value or "").lower()
            if not search_term:
                vendors_table.rows = base_rows
            else:
                filtered = [
                    row for row in base_rows
                    if search_term in (row['vendor_id'] or "").lower()
                    or search_term in (row['vendor_name'] or "").lower()
                    or search_term in (row['contract_manager'] or "").lower()
                    or search_term in (row['contract_backups'] or "").lower()
                ]
                vendors_table.rows = filtered
            vendors_table.update()
        
        def clear_search():
            search_input.value = ""
            filter_vendors()
        
        # Search input for filtering vendors (above the table)
        with ui.row().classes('w-full ml-4 mr-4 mb-6 gap-2 px-2'):
            search_input = ui.input(placeholder='Search by Vendor ID, Vendor Name, Contract Manager, or Backups...').classes(
                'flex-1'
            ).props('outlined dense clearable')
            with search_input.add_slot('prepend'):
                ui.icon('search').classes('text-gray-400')
            ui.button(icon='search', on_click=filter_vendors).props('color=primary')
            ui.button(icon='clear', on_click=clear_search).props('color=secondary')
        
        # Create table after search bar
        initial_rows = vendor_rows
        vendors_table = ui.table(
            columns=vendor_columns,
            column_defaults=vendor_columns_defaults,
            rows=initial_rows,
            pagination=10,
            row_key="vendor_id"
        ).classes("w-full").props("flat bordered").classes(
            "vendors-table shadow-lg rounded-lg overflow-hidden"
        )
        
        search_input.on_value_change(filter_vendors)
        
        # Generate button (moved from header to after table)
        ui.button("Generate", icon="description", on_click=lambda: open_generate_dialog()).props('color=primary').classes('ml-4 mt-4')
        
        # Add custom CSS for visual highlighting
        ui.add_css("""
            .vendors-table thead tr {
                background-color: #144c8e !important;
            }
            .vendors-table tbody tr {
                background-color: white !important;
            }
        """)
        
        # Add slot for vendor ID with clickable link
        vendors_table.add_slot('body-cell-vendor_id', '''
            <q-td :props="props">
                <a :href="'/vendor-info/' + props.row.id" class="text-blue-600 hover:text-blue-800 underline cursor-pointer">
                    {{ props.value }}
                </a>
            </q-td>
        ''')
        
        # Add slot for vendor name with clickable link
        vendors_table.add_slot('body-cell-vendor_name', '''
            <q-td :props="props">
                <a :href="'/vendor-info/' + props.row.id" class="text-blue-600 hover:text-blue-800 underline cursor-pointer">
                    {{ props.value }}
                </a>
            </q-td>
        ''')
        
        # Add slot for days past due with color coding
        vendors_table.add_slot('body-cell-days_past_due', '''
            <q-td :props="props" class="text-right">
                <span v-if="props.value > 0" class="text-red-600 font-semibold">{{ props.value }}</span>
                <span v-else>{{ props.value }}</span>
            </q-td>
        ''')
        
        # Function to generate Excel report
        def open_generate_dialog():
            """Open dialog for report generation"""
            with ui.dialog() as dialog, ui.card().classes('p-6 w-full max-w-md'):
                ui.label("Generate Vendors Due Diligence Report").classes("text-h6 font-bold mb-4")
                
                with ui.column().classes('gap-4 w-full'):
                    ui.label("This report will include all active vendors with their due diligence dates and associated contract managers.").classes("text-sm text-gray-600")
                    
                    with ui.row().classes('gap-2 justify-end w-full mt-4'):
                        ui.button("Cancel", on_click=dialog.close).props('flat')
                        ui.button("Generate & Download", icon="download", 
                                 on_click=lambda: generate_excel_report(dialog)).props('color=primary')
                
                dialog.open()
        
        def generate_excel_report(dialog):
            """Generate Excel report for vendors due diligence"""
            try:
                if not PANDAS_AVAILABLE:
                    ui.notify("Excel export requires pandas library. Please install it: pip install pandas openpyxl", type="negative")
                    dialog.close()
                    return
                
                if not vendor_rows:
                    ui.notify("No vendors available for export", type="warning")
                    dialog.close()
                    return
                
                # Prepare data for Excel with all required fields
                report_data = []
                for vendor in vendor_rows:
                    report_data.append({
                        "Vendor": vendor.get('vendor_name', ''),
                        "Vendor ID": vendor.get('vendor_id', ''),
                        "Last Due Diligence Date": vendor.get('last_due_diligence_date', ''),
                        "Next Required Due Diligence Date": vendor.get('next_required_due_diligence_date', ''),
                        "Days Past Due": vendor.get('days_past_due', 0),
                        "Contract Manager": vendor.get('contract_manager', 'N/A'),
                        "Contract Backups": vendor.get('contract_backups', 'N/A'),
                    })
                
                # Create DataFrame
                df = pd.DataFrame(report_data)
                
                # Create Excel file in memory
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Due Diligence Report')
                    
                    # Get the worksheet
                    worksheet = writer.sheets['Due Diligence Report']
                    
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
                filename = f"Due_Diligence_Report_{today}.xlsx"
                
                # Trigger download using JavaScript
                ui.run_javascript(f'''
                    const link = document.createElement('a');
                    link.href = 'data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64_data}';
                    link.download = '{filename}';
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                ''')
                
                ui.notify(f"Report generated successfully! {len(vendor_rows)} vendor(s) exported.", type="positive")
                dialog.close()
                
            except Exception as e:
                ui.notify(f"Error generating report: {str(e)}", type="negative")
                import traceback
                traceback.print_exc()

