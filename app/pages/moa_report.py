from datetime import datetime, timedelta, date
from nicegui import ui
from app.db.database import SessionLocal
from app.services.contract_service import ContractService
from app.models.contract import ContractStatusType
from app.models.vendor import MaterialOutsourcingType, DocumentType
import io
import base64
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


def moa_report():
    # Navigation
    with ui.row().classes("max-w-6xl mx-auto mt-4"):
        with ui.link(target='/').classes('no-underline'):
            ui.button("Back to Dashboard", icon="arrow_back").props('flat color=primary')
    
    # Global variables for table and data
    contracts_table = None
    contract_rows = []
    
    
    # Fetch MOA contracts from database
    def fetch_moa_contracts():
        """
        Fetches active contracts with Material Outsourcing Agreement = YES.
        This avoids HTTP requests and circular dependencies.
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
            
            # Filter contracts where vendor.material_outsourcing_arrangement = YES
            moa_contracts = [
                contract for contract in contracts
                if contract.vendor and 
                   contract.vendor.material_outsourcing_arrangement == MaterialOutsourcingType.YES
            ]
            
            print(f"Found {len(moa_contracts)} MOA contracts")
            
            # Map contract data to table row format
            rows = []
            for contract in moa_contracts:
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
                
                # Check for vendor documents (4 forms)
                # Risk Assessment Form
                has_risk_assessment = "NO"
                # Business Continuity Plan
                has_business_continuity = "NO"
                # Disaster Recovery Plan
                has_disaster_recovery = "NO"
                # Insurance Policy
                has_insurance_policy = "NO"
                
                if contract.vendor and contract.vendor.documents:
                    for doc in contract.vendor.documents:
                        doc_type = doc.document_type.value if hasattr(doc.document_type, 'value') else str(doc.document_type)
                        if doc_type == DocumentType.RISK_ASSESSMENT_FORM.value:
                            has_risk_assessment = "YES"
                        elif doc_type == DocumentType.BUSINESS_CONTINUITY_PLAN.value:
                            has_business_continuity = "YES"
                        elif doc_type == DocumentType.DISASTER_RECOVERY_PLAN.value:
                            has_disaster_recovery = "YES"
                        elif doc_type == DocumentType.INSURANCE_POLICY.value:
                            has_insurance_policy = "YES"
                
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
                    "risk_assessment": has_risk_assessment,
                    "business_continuity": has_business_continuity,
                    "disaster_recovery": has_disaster_recovery,
                    "insurance_policy": has_insurance_policy,
                })
            
            return rows
            
        except Exception as e:
            print(f"Error fetching MOA contracts: {str(e)}")
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

    contract_rows = fetch_moa_contracts()
    
    # Main container
    with ui.element("div").classes("max-w-6xl mt-8 mx-auto w-full"):
        # Section header with Generate button
        with ui.row().classes('items-center justify-between ml-4 mb-4 w-full'):
            with ui.row().classes('items-center gap-2'):
                ui.icon('description', color='blue').style('font-size: 32px')
                ui.label("Material Outsourcing Agreement Report").classes("text-h5 font-bold")
            
            with ui.row().classes('items-center gap-3'):
                # Generate Report button
                ui.button("Generate", icon="description", on_click=lambda: open_generate_dialog()).props('color=primary')
        
        # Description row
        with ui.row().classes('ml-4 mb-4 w-full'):
            ui.label("Active contracts with Material Outsourcing Agreement = YES").classes(
                "text-sm text-gray-500"
            )
        
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
        
        # Function to generate Excel report
        def open_generate_dialog():
            """Open dialog for report generation"""
            with ui.dialog() as dialog, ui.card().classes('p-6 w-full max-w-md'):
                ui.label("Generate Material Outsourcing Agreement Report").classes("text-h6 font-bold mb-4")
                
                with ui.column().classes('gap-4 w-full'):
                    ui.label("This report will include all active contracts where the vendor has Material Outsourcing Agreement = YES.").classes("text-sm text-gray-600")
                    
                    with ui.row().classes('gap-2 justify-end w-full mt-4'):
                        ui.button("Cancel", on_click=dialog.close).props('flat')
                        ui.button("Generate & Download", icon="download", 
                                 on_click=lambda: generate_excel_report(dialog)).props('color=primary')
                
                dialog.open()
        
        def generate_excel_report(dialog):
            """Generate Excel report for MOA contracts"""
            try:
                if not PANDAS_AVAILABLE:
                    ui.notify("Excel export requires pandas library. Please install it: pip install pandas openpyxl", type="negative")
                    dialog.close()
                    return
                
                if not contract_rows:
                    ui.notify("No MOA contracts available for export", type="warning")
                    dialog.close()
                    return
                
                # Prepare data for Excel with all required fields
                report_data = []
                for contract in contract_rows:
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
                        "Risk Assessment Form": contract.get('risk_assessment', 'NO'),
                        "Business Continuity Plan": contract.get('business_continuity', 'NO'),
                        "Disaster Recovery Plan": contract.get('disaster_recovery', 'NO'),
                        "Insurance Policy": contract.get('insurance_policy', 'NO'),
                    })
                
                # Create DataFrame
                df = pd.DataFrame(report_data)
                
                # Create Excel file in memory
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='MOA Contracts')
                    
                    # Get the worksheet
                    worksheet = writer.sheets['MOA Contracts']
                    
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
                filename = f"MOA_Contracts_Report_{today}.xlsx"
                
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



