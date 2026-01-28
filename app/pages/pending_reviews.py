from datetime import datetime, timedelta, date
from nicegui import ui, app
import io
import base64
from app.db.database import SessionLocal
from app.services.contract_service import ContractService
from app.models.contract import ContractStatusType, ContractTerminationType, User, Contract, ContractUpdate, ContractUpdateStatus
from sqlalchemy.orm import joinedload
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


def pending_reviews():
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
    
    
    # Fetch contracts needing review from database
    def fetch_contracts_needing_review():
        """
        Fetches active contracts expiring within 90 days that need review.
        """
        db = SessionLocal()
        try:
            contract_service = ContractService(db)
            
            # Get contracts needing review (expiring within 90 days)
            contracts, _ = contract_service.get_contracts_needing_review(
                skip=0,
                limit=1000,
                days_ahead=90
            )
            
            print(f"Found {len(contracts)} contracts needing review from database")
            
            if not contracts:
                print("No contracts needing review found in database")
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
                    "status": "Pending review",  # Display status (not from DB)
                    "my_role": str(my_role),
                }
                rows.append(row_data)
            
            print(f"Processed {len(rows)} contract rows")
            return rows
            
        except Exception as e:
            error_msg = f"Error fetching contracts needing review: {str(e)}"
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
    contract_rows = fetch_contracts_needing_review()
    
    # Debug: Check if we have data
    print(f"Total contract rows fetched: {len(contract_rows)}")
    if contract_rows:
        print(f"First row sample: {contract_rows[0]}")
    else:
        ui.notify("No contracts needing review. No active contracts are expiring within 90 days.", type="info")
    
    # Main container
    with ui.element("div").classes("max-w-6xl mt-8 mx-auto w-full"):
        # Section header
        with ui.row().classes('items-center justify-between ml-4 mb-4 w-full'):
            with ui.row().classes('items-center gap-2'):
                ui.icon('edit', color='orange').style('font-size: 32px')
                ui.label("Pending Reviews").classes("text-h5 font-bold")
        
        # Description row
        with ui.row().classes('ml-4 mb-4 w-full'):
            ui.label("Contracts expiring within 90 days that need review").classes(
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
                ui.label("No contracts needing review found").classes("text-lg font-bold text-gray-500")
                ui.label("No active contracts are expiring within 90 days.").classes("text-sm text-gray-400 mt-2")
        
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
        
        # Contract Decision Dialog - same as vendor_info.py
        selected_contract = {}
        
        with ui.dialog() as contract_decision_dialog, ui.card().classes("min-w-[900px] max-w-5xl max-h-[85vh] overflow-y-auto"):
            ui.label("Contract Decision").classes("text-h5 mb-4 text-blue-600")
            
            # Container for dynamic content that gets populated when dialog opens
            dialog_content = ui.column().classes("w-full gap-4")
        
        def populate_dialog_content():
            """Populate dialog content with contract data when opened."""
            dialog_content.clear()
            
            # Fetch latest update for this contract (if any)
            update = None
            contract_obj = None
            acted_by_name = "N/A"
            manager_comments = ""
            
            try:
                db2 = SessionLocal()
                try:
                    contract_obj = db2.query(Contract).options(joinedload(Contract.documents)).filter(Contract.id == selected_contract.get("contract_db_id")).first()
                    update = (
                        db2.query(ContractUpdate)
                        .filter(ContractUpdate.contract_id == selected_contract.get("contract_db_id"))
                        .order_by(ContractUpdate.created_at.desc())
                        .first()
                    )
                    if update and update.response_provided_by_user_id:
                        acted_user = db2.query(User).filter(User.id == update.response_provided_by_user_id).first()
                        if acted_user:
                            acted_by_name = f"{acted_user.first_name} {acted_user.last_name}"
                    if update and update.decision_comments:
                        manager_comments = update.decision_comments
                finally:
                    db2.close()
            except Exception as e:
                print(f"Error loading contract data: {e}")
            
            with dialog_content:
                # Contract details
                with ui.row().classes("mb-4 p-4 bg-gray-50 rounded-lg w-full"):
                    with ui.column().classes("gap-1"):
                        ui.label(f"Contract ID: {selected_contract.get('contract_id', 'N/A')}").classes("font-bold text-lg")
                        ui.label(f"Vendor: {selected_contract.get('vendor_name', 'N/A')}").classes("text-gray-600")
                        ui.label(f"Expiration Date: {selected_contract.get('expiration_date', 'N/A')}").classes("text-gray-600")
                        ui.label(f"Action Taken By: {acted_by_name}").classes("text-gray-600")
                
                # Decision section
                ui.label("Decision").classes("text-lg font-bold")
                decision_select = ui.select(options=["Renew", "Terminate"], value=(update.decision if update and update.decision else "Renew")).props("outlined dense")
                
                # Show manager/backup/owner comments + docs
                ui.label("Documents & Comments").classes("text-lg font-bold mt-2")
                with ui.card().classes("p-4 bg-white border w-full"):
                    ui.label("Comments from Contract Manager / Backup / Owner:").classes("font-medium")
                    ui.textarea(value=manager_comments or "N/A").classes("w-full").props("outlined readonly")
                    
                    ui.separator()
                    ui.label("Contract Documents:").classes("font-medium mt-2")
                    if contract_obj and contract_obj.documents:
                        for doc in contract_obj.documents:
                            with ui.row().classes("items-center justify-between w-full"):
                                ui.label(doc.custom_document_name or doc.file_name).classes("text-sm")
                                with ui.row().classes("gap-2"):
                                    ui.button("Download", icon="download", on_click=lambda p=doc.file_path, n=doc.file_name: ui.download(p, filename=n)).props("flat color=primary")
                    else:
                        ui.label("No contract documents uploaded.").classes("text-gray-500 italic")
                
                # Admin remarks (optional)
                ui.label("Contract Admin Remarks (optional)").classes("font-medium mt-2")
                admin_remarks = ui.textarea(value=(update.admin_comments if update and update.admin_comments else "")).classes("w-full").props("outlined")
                
                # Actions
                with ui.row().classes("gap-3 justify-end mt-4 w-full"):
                    def do_complete():
                        """Complete review:
                        - If decision Extend: update Contract.end_date using manager-provided date
                        - If decision Terminate: set Contract.status to Terminated (inactive)
                        - Mark ContractUpdate as completed and store admin remarks
                        """
                        nonlocal contract_rows
                        try:
                            db3 = SessionLocal()
                            try:
                                upd = (
                                    db3.query(ContractUpdate)
                                    .filter(ContractUpdate.contract_id == selected_contract.get("contract_db_id"))
                                    .order_by(ContractUpdate.created_at.desc())
                                    .first()
                                )
                                if not upd:
                                    upd = ContractUpdate(contract_id=selected_contract.get("contract_db_id"), status=ContractUpdateStatus.COMPLETED)
                                    db3.add(upd)
                                contract_obj_db = db3.query(Contract).filter(Contract.id == selected_contract.get("contract_db_id")).first()
                                if not contract_obj_db:
                                    ui.notify("Error: Contract not found", type="negative")
                                    return

                                decision_value = decision_select.value

                                if decision_value == "Extend":
                                    if not upd.initial_expiration_date:
                                        ui.notify(
                                            "Cannot complete: missing new expiration date from Contract Manager / Backup / Owner.",
                                            type="negative",
                                        )
                                        return
                                    contract_obj_db.end_date = upd.initial_expiration_date
                                    contract_obj_db.last_modified_by = app.storage.user.get("username", "SYSTEM")
                                    contract_obj_db.last_modified_date = datetime.utcnow()
                                elif decision_value == "Terminate":
                                    contract_obj_db.status = ContractStatusType.TERMINATED
                                    contract_obj_db.contract_termination = ContractTerminationType.YES
                                    contract_obj_db.last_modified_by = app.storage.user.get("username", "SYSTEM")
                                    contract_obj_db.last_modified_date = datetime.utcnow()
                                upd.status = ContractUpdateStatus.COMPLETED
                                upd.decision = decision_select.value
                                upd.admin_comments = admin_remarks.value
                                upd.updated_at = datetime.utcnow()
                                db3.commit()
                                ui.notify("Review completed", type="positive")
                                # Refresh the table
                                contract_rows = fetch_contracts_needing_review()
                                contracts_table.rows = contract_rows
                                contracts_table.update()
                            finally:
                                db3.close()
                        except Exception as e:
                            ui.notify(f"Error completing review: {e}", type="negative")
                        contract_decision_dialog.close()
                    
                    def do_send_back():
                        """Send back: mark update returned and save admin remarks."""
                        nonlocal contract_rows
                        try:
                            db3 = SessionLocal()
                            try:
                                upd = (
                                    db3.query(ContractUpdate)
                                    .filter(ContractUpdate.contract_id == selected_contract.get("contract_db_id"))
                                    .order_by(ContractUpdate.created_at.desc())
                                    .first()
                                )
                                if not upd:
                                    upd = ContractUpdate(contract_id=selected_contract.get("contract_db_id"), status=ContractUpdateStatus.RETURNED)
                                    db3.add(upd)
                                upd.status = ContractUpdateStatus.RETURNED
                                upd.decision = decision_select.value
                                upd.admin_comments = admin_remarks.value
                                upd.returned_reason = admin_remarks.value
                                upd.returned_date = datetime.utcnow()
                                upd.updated_at = datetime.utcnow()
                                db3.commit()
                                ui.notify("Sent back to Contract Manager / Backup / Owner", type="info")
                                # Refresh the table
                                contract_rows = fetch_contracts_needing_review()
                                contracts_table.rows = contract_rows
                                contracts_table.update()
                            finally:
                                db3.close()
                        except Exception as e:
                            ui.notify(f"Error sending back: {e}", type="negative")
                        contract_decision_dialog.close()
                    
                    ui.button("Complete", icon="check_circle", on_click=do_complete).props("color=positive")
                    ui.button("Send Back", icon="arrow_back", on_click=do_send_back).props("color=orange")
                    ui.button("Cancel", icon="cancel", on_click=contract_decision_dialog.close).props("flat color=grey")

        # === Pending Review "button" in Status column (NiceGUI/Quasar event-based) ===
        # NiceGUI table slots are Vue templates; instead of relying on globals like `window.*`,
        # we emit a custom event from the slot and handle it in Python via `contracts_table.on(...)`.

        def open_contract_decision_dialog(row: dict) -> None:
            """Open the contract decision dialog for the given table row (dict)."""
            selected_contract.clear()
            selected_contract["contract_id"] = row.get("contract_id", "")
            selected_contract["contract_db_id"] = row.get("id", 0)
            selected_contract["vendor_name"] = row.get("vendor_name", "N/A")
            selected_contract["expiration_date"] = row.get("expiration_date", "N/A")
            populate_dialog_content()
            contract_decision_dialog.open()

        def on_status_click(e) -> None:
            """
            Handle the custom event emitted from the Status cell.
            NiceGUI passes event arguments in `e.args`.
            """
            try:
                row = e.args
                if isinstance(row, dict) and row.get("id") is not None:
                    open_contract_decision_dialog(row)
            except Exception as ex:
                ui.notify(f"Could not open Pending Review dialog: {ex}", type="negative")

        contracts_table.on("status_click", on_status_click)

        # Status column: render a text-like button. On click, emit `status_click` with row payload.
        # `$parent.$emit(...)` is the reliable way within Quasar table slots.
        contracts_table.add_slot('body-cell-status', '''
            <q-td :props="props">
                <q-btn
                    flat
                    no-caps
                    dense
                    icon="pending"
                    :label="props.value"
                    color="orange"
                    class="text-orange-600 font-semibold"
                    style="text-transform:none;"
                    @click="$parent.$emit('status_click', props.row)"
                />
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
                ui.label("Generate Pending Reviews Report").classes("text-h6 font-bold mb-4")
                
                with ui.column().classes('gap-4 w-full'):
                    ui.label("Select date range for pending reviews:").classes("text-sm text-gray-600")
                    
                    start_date_input = ui.input("Start Date", placeholder="YYYY-MM-DD").props('type=date').classes('w-full')
                    end_date_input = ui.input("End Date", placeholder="YYYY-MM-DD").props('type=date').classes('w-full')
                    
                    # Set default dates (last 6 months)
                    today = datetime.now()
                    default_start = (today - timedelta(days=180)).strftime("%Y-%m-%d")
                    default_end = today.strftime("%Y-%m-%d")
                    start_date_input.value = default_start
                    end_date_input.value = default_end
                    
                    ui.label("The report will include all contracts pending reviews.").classes("text-xs text-gray-500 italic")
                    
                    with ui.row().classes('gap-2 justify-end w-full mt-4'):
                        ui.button("Cancel", on_click=dialog.close).props('flat')
                        ui.button("Generate & Download", icon="download", 
                                 on_click=lambda: generate_excel_report(start_date_input.value, end_date_input.value, dialog)).props('color=primary')
                
                dialog.open()
        
        def generate_excel_report(start_date_str, end_date_str, dialog):
            """Generate Excel report for pending reviews"""
            try:
                if not PANDAS_AVAILABLE:
                    ui.notify("Excel export requires pandas library. Please install it: pip install pandas openpyxl", type="negative")
                    dialog.close()
                    return
                
                if not contract_rows:
                    ui.notify("No pending reviews available for export", type="warning")
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
                    df.to_excel(writer, index=False, sheet_name='Pending Reviews')
                    
                    # Get the worksheet
                    worksheet = writer.sheets['Pending Reviews']
                    
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
                filename = f"Pending_Reviews_Report_{start_date_str}_to_{end_date_str}.xlsx"
                
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
