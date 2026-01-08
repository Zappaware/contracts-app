from datetime import datetime, timedelta, date
from nicegui import ui
from app.db.database import SessionLocal
from app.services.contract_service import ContractService
from app.models.contract import ContractStatusType
from decimal import Decimal
import io
import base64
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


def monetary_value_report():
    # Navigation
    with ui.row().classes("max-w-6xl mx-auto mt-4"):
        with ui.link(target='/').classes('no-underline'):
            ui.button("Back to Dashboard", icon="arrow_back").props('flat color=primary')
    
    # Global variables for table and data
    contracts_table = None
    contract_rows = []
    
    
    # Fetch active contracts from database, sorted by contract amount
    def fetch_contracts_by_value(min_amount=None, max_amount=None):
        """
        Fetches active contracts, optionally filtered by amount range, sorted by contract amount (highest to lowest).
        """
        db = SessionLocal()
        try:
            contract_service = ContractService(db)
            
            # Get all active contracts (limit 1000 for display)
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
            
            # Filter by amount range if provided
            filtered_contracts = contracts
            if min_amount is not None or max_amount is not None:
                filtered_contracts = []
                for contract in contracts:
                    contract_amount = float(contract.contract_amount) if contract.contract_amount else 0.0
                    
                    # Check min amount
                    if min_amount is not None and contract_amount < float(min_amount):
                        continue
                    
                    # Check max amount
                    if max_amount is not None and contract_amount > float(max_amount):
                        continue
                    
                    filtered_contracts.append(contract)
            
            # Sort by contract amount (highest to lowest)
            filtered_contracts.sort(
                key=lambda c: float(c.contract_amount) if c.contract_amount else 0.0,
                reverse=True
            )
            
            print(f"Filtered to {len(filtered_contracts)} contracts")
            
            # Map contract data to table row format
            rows = []
            for contract in filtered_contracts:
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
                
                # Format contract amount
                if contract.contract_amount:
                    contract_amount = float(contract.contract_amount)
                    currency = contract.contract_currency.value if hasattr(contract.contract_currency, 'value') else str(contract.contract_currency)
                    formatted_amount = f"{currency} {contract_amount:,.2f}"
                    amount_value = contract_amount
                else:
                    formatted_amount = "N/A"
                    amount_value = 0.0
                
                # Format start date
                if contract.start_date:
                    if isinstance(contract.start_date, date):
                        formatted_start_date = contract.start_date.strftime("%Y-%m-%d")
                    else:
                        formatted_start_date = str(contract.start_date)
                else:
                    formatted_start_date = "N/A"
                
                # Format end date
                if contract.end_date:
                    if isinstance(contract.end_date, date):
                        exp_date = contract.end_date
                        formatted_end_date = exp_date.strftime("%Y-%m-%d")
                        exp_timestamp = datetime.combine(exp_date, datetime.min.time()).timestamp()
                    else:
                        formatted_end_date = str(contract.end_date)
                        exp_timestamp = 0
                else:
                    formatted_end_date = "N/A"
                    exp_timestamp = 0
                
                rows.append({
                    "id": contract.id,  # Internal ID for routing
                    "contract_id": contract.contract_id,
                    "vendor_name": vendor_name,
                    "vendor_id": vendor_id,
                    "contract_type": contract_type,
                    "description": contract.contract_description,
                    "start_date": formatted_start_date,
                    "end_date": formatted_end_date,
                    "expiration_timestamp": exp_timestamp,
                    "status": status,
                    "department": department,
                    "manager": manager_name,
                    "backup": backup_name,
                    "contract_amount": formatted_amount,
                    "amount_value": amount_value,  # For sorting
                })
            
            return rows
            
        except Exception as e:
            print(f"Error fetching contracts by value: {str(e)}")
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
            "label": "Vendor",
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
            "label": "Description",
            "field": "description",
            "align": "left",
        },
        {
            "name": "contract_amount",
            "label": "Contract Amount",
            "field": "amount_value",
            "align": "right",
            "sortable": True,
            "sort-order": "da",  # Descending/Ascending - default to descending
        },
        {
            "name": "start_date",
            "label": "Start Date",
            "field": "start_date",
            "align": "left",
            "sortable": True,
        },
        {
            "name": "end_date",
            "label": "End Date",
            "field": "end_date",
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
            "name": "manager",
            "label": "Contract Manager",
            "field": "manager",
            "align": "left",
            "sortable": True,
        },
    ]

    contract_columns_defaults = {
        "align": "left",
        "headerClasses": "bg-[#144c8e] text-white",
    }

    # Initial load without filters
    contract_rows = fetch_contracts_by_value()
    
    # Main container
    with ui.element("div").classes("max-w-6xl mt-8 mx-auto w-full"):
        # Section header with Generate button
        with ui.row().classes('items-center justify-between ml-4 mb-4 w-full'):
            with ui.row().classes('items-center gap-2'):
                ui.icon('attach_money', color='green').style('font-size: 32px')
                ui.label("Contracts Monetary Value Report").classes("text-h5 font-bold")
            
            with ui.row().classes('items-center gap-3'):
                # Generate Report button
                ui.button("Generate", icon="description", on_click=lambda: open_generate_dialog()).props('color=primary')
        
        # Description row
        with ui.row().classes('ml-4 mb-4 w-full'):
            ui.label("Active contracts sorted by monetary value (highest to lowest)").classes(
                "text-sm text-gray-500"
            )
        
        # Amount range filter section
        with ui.card().classes('ml-4 mr-4 mb-4 p-4'):
            with ui.column().classes('gap-3'):
                ui.label("Filter by Amount Range (Optional)").classes("text-sm font-semibold text-gray-700")
                with ui.row().classes('gap-4 items-end'):
                    from_amount_filter = ui.input("From Amount", placeholder="Optional - minimum amount").props('type=number').classes('flex-1')
                    to_amount_filter = ui.input("To Amount", placeholder="Optional - maximum amount").props('type=number').classes('flex-1')
                    
                    def apply_filters():
                        """Apply amount filters and refresh table"""
                        nonlocal contract_rows
                        from_val = from_amount_filter.value.strip() if from_amount_filter.value else None
                        to_val = to_amount_filter.value.strip() if to_amount_filter.value else None
                        
                        try:
                            min_amount = float(from_val) if from_val else None
                            max_amount = float(to_val) if to_val else None
                        except ValueError:
                            ui.notify("Invalid amount values. Please enter valid numbers.", type="negative")
                            return
                        
                        # Validate range
                        if min_amount is not None and max_amount is not None and min_amount > max_amount:
                            ui.notify("'From Amount' must be less than or equal to 'To Amount'.", type="negative")
                            return
                        
                        # Refresh data with filters
                        contract_rows = fetch_contracts_by_value(min_amount, max_amount)
                        contracts_table.rows = contract_rows
                        contracts_table.update()
                        count_label.text = f"Total: {len(contract_rows)} contract(s)"
                        ui.notify(f"Filtered to {len(contract_rows)} contract(s)", type="positive")
                    
                    def clear_filters():
                        """Clear filters and show all contracts"""
                        nonlocal contract_rows
                        from_amount_filter.value = ""
                        to_amount_filter.value = ""
                        contract_rows = fetch_contracts_by_value()
                        contracts_table.rows = contract_rows
                        contracts_table.update()
                        count_label.text = f"Total: {len(contract_rows)} contract(s)"
                        ui.notify("Filters cleared", type="info")
                    
                    ui.button("Apply Filters", icon="filter_list", on_click=apply_filters).props('color=primary')
                    ui.button("Clear", icon="clear", on_click=clear_filters).props('flat')
        
        # Count label row
        with ui.row().classes('ml-4 mb-2'):
            count_label = ui.label(f"Total: {len(contract_rows)} contract(s)").classes("text-sm text-gray-500")
        
        # Define search functions first
        def filter_contracts():
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
            filter_contracts()
        
        # Search input for filtering contracts (above the table)
        with ui.row().classes('w-full ml-4 mr-4 mb-6 gap-2 px-2'):
            search_input = ui.input(placeholder='Search by Contract ID, Vendor, Type, Description, or Manager...').classes(
                'flex-1'
            ).props('outlined dense clearable')
            with search_input.add_slot('prepend'):
                ui.icon('search').classes('text-gray-400')
            ui.button(icon='search', on_click=filter_contracts).props('color=primary')
            ui.button(icon='clear', on_click=clear_search).props('color=secondary')
        
        # Create table after search bar
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
        
        # Add custom CSS for visual highlighting
        ui.add_css("""
            .contracts-table thead tr {
                background-color: #144c8e !important;
            }
            .contracts-table tbody tr {
                background-color: white !important;
            }
        """)
        
        # Add slot for contract ID with clickable link
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
        
        # Add slot for contract amount with right alignment
        contracts_table.add_slot('body-cell-contract_amount', '''
            <q-td :props="props" class="text-right">
                {{ props.value }}
            </q-td>
        ''')
        
        # Function to generate Excel report
        def open_generate_dialog():
            """Open dialog for amount range selection and report generation"""
            with ui.dialog() as dialog, ui.card().classes('p-6 w-full max-w-md'):
                ui.label("Generate Monetary Value Report").classes("text-h6 font-bold mb-4")
                
                with ui.column().classes('gap-4 w-full'):
                    ui.label("Optionally filter by contract amount range:").classes("text-sm text-gray-600 font-semibold")
                    
                    from_amount_input = ui.input("From Amount", placeholder="Optional - minimum amount").props('type=number').classes('w-full')
                    to_amount_input = ui.input("To Amount", placeholder="Optional - maximum amount").props('type=number').classes('w-full')
                    
                    ui.label("Leave fields empty to include all active contracts. Amounts are in the contract's currency.").classes("text-xs text-gray-500 italic")
                    ui.label("Contracts will be sorted by amount from highest to lowest.").classes("text-xs text-gray-500 italic")
                    
                    with ui.row().classes('gap-2 justify-end w-full mt-4'):
                        ui.button("Cancel", on_click=dialog.close).props('flat')
                        ui.button("Generate & Download", icon="download", 
                                 on_click=lambda: generate_excel_report(from_amount_input.value, to_amount_input.value, dialog)).props('color=primary')
                
                dialog.open()
        
        def generate_excel_report(from_amount_str, to_amount_str, dialog):
            """Generate Excel report for contracts by monetary value"""
            try:
                if not PANDAS_AVAILABLE:
                    ui.notify("Excel export requires pandas library. Please install it: pip install pandas openpyxl", type="negative")
                    dialog.close()
                    return
                
                # Parse amount range if provided
                min_amount = None
                max_amount = None
                
                if from_amount_str and from_amount_str.strip():
                    try:
                        min_amount = float(from_amount_str.strip())
                    except ValueError:
                        ui.notify("Invalid 'From Amount' value. Please enter a valid number.", type="negative")
                        return
                
                if to_amount_str and to_amount_str.strip():
                    try:
                        max_amount = float(to_amount_str.strip())
                    except ValueError:
                        ui.notify("Invalid 'To Amount' value. Please enter a valid number.", type="negative")
                        return
                
                # Validate range
                if min_amount is not None and max_amount is not None and min_amount > max_amount:
                    ui.notify("'From Amount' must be less than or equal to 'To Amount'.", type="negative")
                    return
                
                # Fetch contracts with amount filter
                filtered_contract_rows = fetch_contracts_by_value(min_amount, max_amount)
                
                if not filtered_contract_rows:
                    ui.notify("No contracts found matching the specified criteria.", type="warning")
                    dialog.close()
                    return
                
                # Prepare data for Excel with all required fields
                report_data = []
                for contract in filtered_contract_rows:
                    # Extract just the amount value for the report (without currency)
                    amount_value = contract.get('amount_value', 0.0)
                    currency = "USD"  # Default, could be extracted from contract if needed
                    
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
                        "Contract Amount": amount_value,
                    })
                
                # Create DataFrame
                df = pd.DataFrame(report_data)
                
                # Create Excel file in memory
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Monetary Value Report')
                    
                    # Get the worksheet
                    worksheet = writer.sheets['Monetary Value Report']
                    
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
                    
                    # Format Contract Amount column as currency (right-aligned)
                    try:
                        from openpyxl.styles import Alignment
                        amount_col = None
                        for idx, col in enumerate(worksheet.columns, 1):
                            if worksheet.cell(1, idx).value == "Contract Amount":
                                amount_col = idx
                                break
                        
                        if amount_col:
                            for row in range(2, len(report_data) + 2):
                                cell = worksheet.cell(row, amount_col)
                                cell.number_format = '#,##0.00'  # Number format with thousands separator
                                cell.alignment = Alignment(horizontal='right')
                    except ImportError:
                        # If openpyxl styles not available, skip formatting
                        pass
                
                output.seek(0)
                
                # Convert to base64 for download
                excel_data = output.getvalue()
                b64_data = base64.b64encode(excel_data).decode()
                
                # Generate filename
                today = datetime.now().strftime("%Y-%m-%d")
                range_text = ""
                if min_amount is not None or max_amount is not None:
                    range_text = f"_Range_{min_amount or 0}-{max_amount or 'unlimited'}"
                filename = f"Monetary_Value_Report_{today}{range_text}.xlsx"
                
                # Trigger download using JavaScript
                ui.run_javascript(f'''
                    const link = document.createElement('a');
                    link.href = 'data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64_data}';
                    link.download = '{filename}';
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                ''')
                
                ui.notify(f"Report generated successfully! {len(filtered_contract_rows)} contract(s) exported.", type="positive")
                dialog.close()
                
            except Exception as e:
                ui.notify(f"Error generating report: {str(e)}", type="negative")
                import traceback
                traceback.print_exc()

