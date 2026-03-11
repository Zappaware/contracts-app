"""All Contracts page - lists contracts of any status (active, expired, terminated, etc.)."""
from datetime import datetime, timedelta, date
from nicegui import ui, app
from app.db.database import SessionLocal
from app.services.contract_service import ContractService
from app.models.contract import ContractStatusType, User, UserRole
from app.utils.navigation import get_dashboard_url
from app.components.breadcrumb import breadcrumb
import io
import base64
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


def all_contracts():
    current_user_id = app.storage.user.get('user_id', None)
    current_user_role = app.storage.user.get('user_role', None)

    if not current_user_id:
        current_username = app.storage.user.get('username', None)
        try:
            db = SessionLocal()
            try:
                if current_username:
                    current_user = db.query(User).filter(User.email == current_username).first()
                    if not current_user:
                        current_user = db.query(User).filter(User.email.ilike(f"%{current_username}%")).first()
                    if not current_user:
                        current_user = db.query(User).filter(User.first_name.ilike(f"%{current_username}%")).first()
                    if current_user:
                        current_user_id = current_user.id
                        current_user_role = current_user.role.value if current_user.role else None
            finally:
                db.close()
        except Exception as e:
            print(f"Error fetching current user: {e}")

    with ui.row().classes("max-w-6xl mx-auto mt-4"):
        breadcrumb([("Home", get_dashboard_url()), ("All Contracts", None)])

    contract_rows = []

    def fetch_all_contracts():
        db = SessionLocal()
        try:
            contract_service = ContractService(db)
            contracts, _ = contract_service.search_and_filter_contracts(
                skip=0,
                limit=1000,
                search=None,
                status=None,
                contract_type=None,
                department=None,
                owner_id=None,
                vendor_id=None,
                expiring_soon=None
            )

            if current_user_role == UserRole.CONTRACT_ADMIN.value:
                pass  # Admin sees all contracts
            elif current_user_role in [UserRole.CONTRACT_MANAGER.value, UserRole.CONTRACT_MANAGER_BACKUP.value, UserRole.CONTRACT_MANAGER_OWNER.value]:
                if current_user_id:
                    contracts = [
                        c for c in contracts
                        if (c.contract_owner_id == current_user_id or
                            c.contract_owner_backup_id == current_user_id or
                            c.contract_owner_manager_id == current_user_id)
                    ]
                else:
                    contracts = []
            else:
                contracts = []

            rows = []
            for contract in contracts:
                backup_name = f"{contract.contract_owner_backup.first_name} {contract.contract_owner_backup.last_name}" if contract.contract_owner_backup else "N/A"
                vendor_name = contract.vendor.vendor_name if contract.vendor else "Unknown"
                vendor_id = contract.vendor.id if contract.vendor else None
                contract_type = contract.contract_type.value if hasattr(contract.contract_type, 'value') else str(contract.contract_type)
                status = contract.status.value if hasattr(contract.status, 'value') else str(contract.status)
                department = contract.department.value if hasattr(contract.department, 'value') else str(contract.department)
                automatic_renewal = contract.automatic_renewal.value if hasattr(contract.automatic_renewal, 'value') else str(contract.automatic_renewal)

                formatted_start_date = contract.start_date.strftime("%Y-%m-%d") if contract.start_date else "N/A"
                if contract.end_date:
                    exp_date = contract.end_date
                    formatted_date = exp_date.strftime("%Y-%m-%d")
                    exp_timestamp = datetime.combine(exp_date, datetime.min.time()).timestamp()
                    month = exp_date.month
                    year = exp_date.year
                    ending_quarter = f"Q{(month - 1) // 3 + 1} {year}"
                else:
                    formatted_date = "N/A"
                    exp_timestamp = 0
                    ending_quarter = "N/A"

                my_role = "N/A"
                if current_user_id:
                    if contract.contract_owner_id == current_user_id:
                        my_role = "Contract Manager"
                    elif contract.contract_owner_backup_id == current_user_id:
                        my_role = "Backup"
                    elif contract.contract_owner_manager_id == current_user_id:
                        my_role = "Owner"

                status_color = "green" if contract.status == ContractStatusType.ACTIVE else "red" if contract.status == ContractStatusType.TERMINATED else "orange"

                rows.append({
                    "id": int(contract.id),
                    "contract_id": str(contract.contract_id or ""),
                    "vendor_id": int(vendor_id) if vendor_id else 0,
                    "vendor_name": str(vendor_name or ""),
                    "contract_type": str(contract_type or ""),
                    "description": str(contract.contract_description or ""),
                    "start_date": str(formatted_start_date),
                    "end_date": str(formatted_date),
                    "expiration_date": str(formatted_date),
                    "expiration_timestamp": float(exp_timestamp),
                    "ending_quarter": str(ending_quarter),
                    "automatic_renewal": str(automatic_renewal),
                    "department": str(department),
                    "status": str(status or "Unknown"),
                    "status_color": str(status_color),
                    "my_role": str(my_role),
                    "backup": str(backup_name),
                })
            return rows
        except Exception as e:
            print(f"Error fetching contracts: {e}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            db.close()

    contract_rows = fetch_all_contracts()

    contract_columns = [
        {"name": "contract_id", "label": "Contract ID", "field": "contract_id", "align": "left", "sortable": True},
        {"name": "vendor_name", "label": "Vendor Name", "field": "vendor_name", "align": "left", "sortable": True},
        {"name": "contract_type", "label": "Contract Type", "field": "contract_type", "align": "left", "sortable": True},
        {"name": "description", "label": "Description", "field": "description", "align": "left"},
        {"name": "expiration_date", "label": "Expiration Date", "field": "expiration_date", "align": "left", "sortable": True},
        {"name": "status", "label": "Status", "field": "status", "align": "left"},
        {"name": "my_role", "label": "My Role", "field": "my_role", "align": "left", "sortable": True},
    ]

    contract_columns_defaults = {"align": "left", "headerClasses": "bg-[#144c8e] text-white"}

    with ui.element("div").classes("max-w-6xl mt-8 mx-auto w-full"):
        with ui.row().classes('items-center justify-between ml-4 mb-4 w-full'):
            with ui.row().classes('items-center gap-2'):
                ui.icon('list', color='primary').style('font-size: 32px')
                ui.label("All Contracts").classes("text-h5 font-bold")

        with ui.row().classes('ml-4 mb-4 w-full'):
            ui.label("Contracts of any status: active, expired, terminated, etc.").classes("text-sm text-gray-500")

        with ui.row().classes('ml-4 mb-2'):
            ui.label(f"Total: {len(contract_rows)} contracts").classes("text-sm text-gray-500")

        def filter_contracts():
            search_term = (search_input.value or "").lower()
            if not search_term:
                contracts_table.rows = contract_rows
            else:
                filtered = [
                    row for row in contract_rows
                    if search_term in (row.get('contract_id') or "").lower()
                    or search_term in (row.get('vendor_name') or "").lower()
                    or search_term in (row.get('contract_type') or "").lower()
                    or search_term in (row.get('description') or "").lower()
                    or search_term in (row.get('status') or "").lower()
                    or search_term in (row.get('my_role') or "").lower()
                ]
                contracts_table.rows = filtered
            contracts_table.update()

        def clear_search():
            search_input.value = ""
            filter_contracts()

        with ui.row().classes('w-full ml-4 mr-4 mb-6 gap-2 px-2'):
            search_input = ui.input(placeholder='Search by Contract ID, Vendor, Type, Description, Status, or My Role...').classes(
                'flex-1'
            ).props('outlined dense clearable')
            with search_input.add_slot('prepend'):
                ui.icon('search').classes('text-gray-400')
            ui.button(icon='search', on_click=filter_contracts).props('color=primary')
            ui.button(icon='clear', on_click=clear_search).props('color=secondary')

        if not contract_rows:
            with ui.card().classes("w-full p-6"):
                ui.label("No contracts found").classes("text-lg font-bold text-gray-500")
                ui.label("Contracts will appear here when they are created.").classes("text-sm text-gray-400 mt-2")

        contracts_table = ui.table(
            columns=contract_columns,
            column_defaults=contract_columns_defaults,
            rows=contract_rows,
            pagination=10,
            row_key="id"
        ).classes("w-full").props("flat bordered").classes("contracts-table shadow-lg rounded-lg overflow-hidden")

        ui.button("Generate", icon="description", on_click=lambda: open_generate_dialog()).props('color=primary').classes('ml-4 mt-4')
        search_input.on_value_change(filter_contracts)

        ui.add_css("""
            .contracts-table thead tr { background-color: #144c8e !important; }
        """)

        contracts_table.add_slot('body-cell-contract_id', '''
            <q-td :props="props">
                <a :href="'/contract-info/' + props.row.id" class="text-blue-600 hover:text-blue-800 underline cursor-pointer">
                    {{ props.value }}
                </a>
            </q-td>
        ''')

        contracts_table.add_slot('body-cell-vendor_name', '''
            <q-td :props="props">
                <a :href="'/vendor-info/' + props.row.vendor_id" class="text-blue-600 hover:text-blue-800 underline cursor-pointer">
                    {{ props.value }}
                </a>
            </q-td>
        ''')

        contracts_table.add_slot('body-cell-status', '''
            <q-td :props="props">
                <q-badge
                    :color="props.row.status_color === 'green' ? 'positive' : (props.row.status_color === 'red' ? 'negative' : 'warning')"
                    :label="props.value"
                />
            </q-td>
        ''')

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

        def open_generate_dialog():
            with ui.dialog() as dialog, ui.card().classes('p-6 w-full max-w-md'):
                ui.label("Generate All Contracts Report").classes("text-h6 font-bold mb-4")
                with ui.column().classes('gap-4 w-full'):
                    ui.label("Export all contracts to Excel.").classes("text-sm text-gray-600")
                    with ui.row().classes('gap-2 justify-end w-full mt-4'):
                        ui.button("Cancel", on_click=dialog.close).props('flat')
                        ui.button("Generate & Download", icon="download",
                                 on_click=lambda: generate_excel_report(dialog)).props('color=primary')
                dialog.open()

        def generate_excel_report(dialog):
            try:
                if not contract_rows:
                    ui.notify("No contracts available for export", type="warning")
                    dialog.close()
                    return
                if not PANDAS_AVAILABLE:
                    ui.notify("Excel export requires pandas. Please install: pip install pandas openpyxl", type="negative")
                    dialog.close()
                    return
                report_data = []
                for c in contract_rows:
                    report_data.append({
                        "Vendor": c.get('vendor_name', ''),
                        "Contract ID": c.get('contract_id', ''),
                        "Contract Type": c.get('contract_type', ''),
                        "Description": c.get('description', ''),
                        "Start Date": c.get('start_date', ''),
                        "End Date": c.get('end_date', ''),
                        "Status": c.get('status', ''),
                        "Department": c.get('department', ''),
                        "My Role": c.get('my_role', ''),
                    })
                df = pd.DataFrame(report_data)
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='All Contracts')
                output.seek(0)
                b64_data = base64.b64encode(output.getvalue()).decode()
                filename = f"All_Contracts_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
                ui.run_javascript(f'''
                    const link = document.createElement('a');
                    link.href = 'data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64_data}';
                    link.download = '{filename}';
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                ''')
                ui.notify(f"Report generated! {len(contract_rows)} contract(s) exported.", type="positive")
                dialog.close()
            except Exception as e:
                ui.notify(f"Error generating report: {str(e)}", type="negative")
