
from datetime import datetime, timedelta, date

import requests
from nicegui import ui, app
from app.utils.vendor_lookup import get_vendor_id_by_name
from app.db.database import SessionLocal
from app.models.contract import Contract, ContractUpdate, ContractUpdateStatus, User, ContractStatusType, ContractTerminationType
from sqlalchemy.orm import joinedload


def home_page():
    # Global variables for table and data
    contracts_table = None
    contract_rows = []
    
    # Fetch vendor count from database
    vendor_count = 0
    try:
        from app.db.database import SessionLocal
        from app.services.vendor_service import VendorService
        db = SessionLocal()
        try:
            vendor_service = VendorService(db)
            _, vendor_count = vendor_service.get_vendors_with_filters(skip=0, limit=1, status_filter=None, search=None)
        finally:
            db.close()
    except Exception as e:
        print(f"Error fetching vendor count: {e}")
        vendor_count = 0
    
    # Fetch active contracts count from database
    active_contracts_count = 0
    try:
        from app.services.contract_service import ContractService
        from app.models.contract import ContractStatusType
        db = SessionLocal()
        try:
            contract_service = ContractService(db)
            _, active_contracts_count = contract_service.search_and_filter_contracts(
                skip=0,
                limit=1,
                status=ContractStatusType.ACTIVE,
                search=None,
                contract_type=None,
                department=None,
                owner_id=None,
                vendor_id=None,
                expiring_soon=None
            )
        finally:
            db.close()
    except Exception as e:
        print(f"Error fetching active contracts count: {e}")
        active_contracts_count = 0

    # Fetch contracts requiring attention count (expiring soon or past due)
    contracts_requiring_attention_count = 0
    try:
        from app.db.database import SessionLocal
        from app.services.contract_service import ContractService
        db = SessionLocal()
        try:
            contract_service = ContractService(db)
            _, contracts_requiring_attention_count = contract_service.get_contracts_requiring_attention(
                skip=0, limit=1, days_ahead=30
            )
        finally:
            db.close()
    except Exception as e:
        print(f"Error fetching contracts requiring attention count: {e}")
        contracts_requiring_attention_count = 0

    # Function to show the contracts table
    def show_contracts_table():
        contracts_table_container.visible = True
        # recent_activity_container.visible = False  # Commented out - Recent Activity is hidden
    
    # Function to handle owned/backup toggle
    
    # Quick Stats Cards (shrink to table width)
    with ui.element("div").classes("max-w-7xl mx-auto w-full"):
        with ui.row().classes(
            "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 mt-8 gap-6 w-full items-start"
        ):
            # Row 1
            with ui.link(target='/active-contracts').classes('no-underline w-full').style('text-decoration: none !important;'):
                with ui.card().classes("w-full cursor-pointer hover:bg-gray-50 transition-colors shadow-lg").props('flat'):
                    with ui.row().classes('items-center gap-2'):
                        ui.icon('article', color='primary').style('font-size: 28px')
                        ui.label("Active Contracts").classes("text-lg font-bold")
                    ui.label("Currently active contracts").classes("text-sm text-gray-500 mt-2")
                    ui.label(str(active_contracts_count)).classes("text-2xl font-medium text-primary mt-2")
            with ui.link(target='/pending-contracts').classes('no-underline w-full').style('text-decoration: none !important;'):
                with ui.card().classes("w-full cursor-pointer hover:bg-gray-50 transition-colors shadow-lg").props('flat'):
                    with ui.row().classes('items-center gap-2'):
                        ui.icon('edit', color='primary').style('font-size: 28px')
                        ui.label("Pending Documents").classes("text-lg font-bold")
                    ui.label("Contracts missing documents").classes("text-sm text-gray-500 mt-2")
                    ui.label("12").classes("text-2xl font-medium text-primary mt-2")
            with ui.link(target='/contract-managers').classes('no-underline w-full').style('text-decoration: none !important;'):
                with ui.card().classes("w-full cursor-pointer hover:bg-gray-50 transition-colors shadow-lg").props('flat'):
                    with ui.row().classes('items-center gap-2'):
                        ui.icon('people', color='primary').style('font-size: 28px')
                        ui.label("User Administration").classes("text-lg font-bold")
                    ui.label("View user responsibilities").classes("text-sm text-gray-500 mt-2")
                    ui.label("15").classes("text-2xl font-medium text-primary mt-2")

            # Row 2
            with ui.link(target='/pending-reviews').classes('no-underline w-full').style('text-decoration: none !important;'):
                with ui.card().classes("w-full cursor-pointer hover:bg-gray-50 transition-colors shadow-lg").props('flat'):
                    with ui.row().classes('items-center gap-2'):
                        ui.icon('pending', color='primary').style('font-size: 28px')
                        ui.label("Pending Reviews").classes("text-lg font-bold")
                    ui.label("Contracts awaiting review").classes("text-sm text-gray-500 mt-2")
                    ui.label("23").classes("text-2xl font-medium text-primary mt-2")
            with ui.link(target='/vendors').classes('no-underline w-full').style('text-decoration: none !important;'):
                with ui.card().classes("w-full cursor-pointer hover:bg-gray-50 transition-colors shadow-lg").props('flat'):
                    with ui.row().classes('items-center gap-2'):
                        ui.icon('business', color='primary').style('font-size: 28px')
                        ui.label("Vendors List").classes("text-lg font-bold")
                    ui.label("View all registered vendors").classes("text-sm text-gray-500 mt-2")
                    ui.label(str(vendor_count)).classes("text-2xl font-medium text-primary mt-2")
            with ui.card().classes("w-full cursor-pointer hover:bg-gray-50 transition-colors shadow-lg").props('flat').on('click', show_contracts_table):
                with ui.row().classes('items-center gap-2'):
                    ui.icon('warning', color='primary').style('font-size: 28px')
                    ui.label("Contracts Requiring Attention").classes("text-lg font-bold")
                ui.label("Contracts approaching or past their expiration date").classes("text-sm text-gray-500 mt-2")
                ui.label(str(contracts_requiring_attention_count)).classes("text-2xl font-medium text-primary mt-2")
            with ui.link(target='/contract-updates').classes('no-underline w-full').style('text-decoration: none !important;'):
                with ui.card().classes("w-full cursor-pointer hover:bg-gray-50 transition-colors shadow-lg").props('flat'):
                    with ui.row().classes('items-center gap-2'):
                        ui.icon('update', color='primary').style('font-size: 28px')
                        ui.label("Contract Updates").classes("text-lg font-bold")
                    ui.label("Review manager responses and updates").classes("text-sm text-gray-500 mt-2")
                    ui.label("15").classes("text-2xl font-medium text-primary mt-2")

    # ===== COMMENTED OUT: Recent Activity Section =====
    # Container for the Recent Activity section
    # recent_activity_container = ui.element("div").classes("max-w-6xl mt-8 mx-auto w-full")
    # 
    # with recent_activity_container:
    #     with ui.card().classes("mt-8 w-full"):
    #         ui.label("Recent Activity").classes("text-lg font-bold")
    #         ui.label("Latest contract management activities").classes(
    #             "text-sm text-gray-500 mb-4"
    #         )
    #         with ui.column().classes("space-y-4 w-full"):
    #             with ui.row().classes(
    #                 "flex items-center justify-between py-2 border-b border-gray-200 last:border-b-0 w-full"
    #             ):
    #                 with ui.column():
    #                     ui.label("New contract created").classes("font-medium")
    #                     ui.label("Contract #CTR-2024-001 with ABC Corp").classes(
    #                         "text-sm text-gray-500"
    #                     )
    #                 ui.label("2 hours ago").classes("text-sm text-gray-500")
    #             with ui.row().classes(
    #                 "flex items-center justify-between py-2 border-b border-gray-200 last:border-b-0 w-full"
    #             ):
    #                 with ui.column():
    #                     ui.label("Vendor registered").classes("font-medium")
    #                     ui.label("XYZ Services added to vendor database").classes(
    #                         "text-sm text-gray-500"
    #                     )
    #                 ui.label("4 hours ago").classes("text-sm text-gray-500")
    #             with ui.row().classes(
    #                 "flex items-center justify-between py-2 border-b border-gray-200 last:border-b-0 w-full"
    #             ):
    #                 with ui.column():
    #                     ui.label("Contract approved").classes("font-medium")
    #                     ui.label(
    #                         "Contract #CTR-2024-002 approved by management"
    #                     ).classes("text-sm text-gray-500")
    #                 ui.label("1 day ago").classes("text-sm text-gray-500")

    # ===== COMMENTED OUT: Vendor List Section =====
    # with ui.element("div").classes("max-w-6xl mt-8 mx-auto w-full"):
    #     ui.label("Vendor List").classes("text-h5 ml-4 font-bold ")
    #
    # columns = [
    #     {
    #         "name": "id",
    #         "label": "Id",
    #         "field": "id",
    #         "align": "left",
    #     },
    #     {
    #         "name": "name",
    #         "label": "Name",
    #         "field": "name",
    #         "align": "left",
    #     },
    #     {
    #         "name": "contact",
    #         "label": "Contact Person",
    #         "field": "contact",
    #         "align": "left",
    #     },
    #     {
    #         "name": "country",
    #         "label": "Country",
    #         "field": "country",
    #         "align": "left",
    #     },
    #     {
    #         "name": "telephone",
    #         "label": "Telephone",
    #         "field": "telephone",
    #         "align": "left",
    #     },
    #     {
    #         "name": "email",
    #         "label": "Email",
    #         "field": "email",
    #         "align": "left",
    #     },
    #     {
    #         "name": "D.D. Performed",
    #         "label": "D.D. Performed",
    #         "field": "dd_performed",
    #         "align": "left",
    #     },
    #     {
    #         "name": "attention",
    #         "label": "Attention",
    #         "field": "attention",
    #         "align": "left",
    #     },
    # ]
    # columns_defaults = {
    #     "align": "left",
    #     "headerClasses": "bg-[#144c8e] text-white",
    # }
    # def fetch_vendors():
    #     url = "http://localhost:8000/api/v1/vendors/"
    #     try:
    #         response = requests.get(url)
    #         response.raise_for_status()
    #         vendor_list = response.json()
    #         # Map backend vendor data to table row format
    #         rows = []
    #         for v in vendor_list:
    #             rows.append({
    #                 "id": v.get("id", ""),
    #                 "name": v.get("vendor_name", ""),
    #                 "contact": v.get("vendor_contact_person", ""),
    #                 "country": v.get("vendor_country", ""),
    #                 "telephone": v.get("phones", [{}])[0].get("phone_number", "") if v.get("phones") else "",
    #                 "email": v.get("emails", [{}])[0].get("email", "") if v.get("emails") else "",
    #                 "dd_performed": "Yes" if v.get("due_diligence_required", "No") == "Yes" else "No",
    #                 "attention": v.get("attention", "")
    #             })
    #         return rows
    #     except Exception as e:
    #         ui.notify(f"Error fetching vendors: {e}", type="negative")
    #         return []
    #
    # rows = fetch_vendors()
    #
    # with ui.element("div").classes("max-w-6xl mx-auto w-full"):
    #     ui.table(
    #         columns=columns, column_defaults=columns_defaults, rows=rows, pagination=3
    #     ).classes("w-full").props("flat").classes(
    #         "vendor-table shadow-lg rounded-lg overflow-hidden"
    #     )
    #     ui.add_css(".vendor-table thead tr { background-color: #144c8e !important; }")

    
    # ===== NEW SECTION: Contracts Requiring Attention =====

    def get_contracts_requiring_attention():
        """
        Fetch contracts that are expiring soon or have reached their end date
        from the backend. Status logic matches mock: "X days past due" (red)
        or "X days remaining" (yellow).
        """
        today = date.today()
        rows = []
        try:
            from app.db.database import SessionLocal
            from app.services.contract_service import ContractService

            db = SessionLocal()
            try:
                contract_service = ContractService(db)
                contracts, _ = contract_service.get_contracts_requiring_attention(
                    skip=0,
                    limit=1000,
                    days_ahead=30
                )

                for contract in contracts:
                    exp_date = contract.end_date
                    days_diff = (today - exp_date).days

                    # Calculate status and visual indicators (based on mock logic)
                    if days_diff > 0:
                        # Past due - RED
                        status = f"{days_diff} days past due"
                        status_class = "expired"
                        row_class = "bg-red-50"
                    else:
                        # Approaching expiration - WARNING
                        status = f"{abs(days_diff)} days remaining"
                        status_class = "warning"
                        row_class = "bg-yellow-50"

                    vendor_name = contract.vendor.vendor_name if contract.vendor else "Unknown"
                    vendor_id = contract.vendor.id if contract.vendor else None
                    contract_type = contract.contract_type.value if hasattr(contract.contract_type, 'value') else str(contract.contract_type)
                    manager_name = f"{contract.contract_owner.first_name} {contract.contract_owner.last_name}" if contract.contract_owner else "Unknown"

                    rows.append({
                        "id": contract.id,
                        "contract_id": contract.contract_id,
                        "vendor_name": vendor_name,
                        "vendor_id": vendor_id,
                        "contract_type": contract_type,
                        "description": contract.contract_description or "",
                        "expiration_date": exp_date.strftime("%Y-%m-%d"),
                        "expiration_timestamp": datetime.combine(exp_date, datetime.min.time()).timestamp(),
                        "status": status,
                        "status_class": status_class,
                        "row_class": row_class,
                        "manager": manager_name,
                    })
            finally:
                db.close()
        except Exception as e:
            print(f"Error fetching contracts requiring attention: {e}")
            import traceback
            traceback.print_exc()
        return rows

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

    contract_rows = get_contracts_requiring_attention()
    
    # Container for the contracts table (initially hidden)
    contracts_table_container = ui.element("div").classes("max-w-7xl mt-8 mx-auto w-full")
    contracts_table_container.visible = False
    
    with contracts_table_container:
        # Section header - left-aligned with table
        with ui.row().classes('items-center justify-start mb-4 w-full px-4'):
            with ui.row().classes('items-center gap-2'):
                ui.icon('warning', color='orange').style('font-size: 32px')
                ui.label("Contracts Requiring Attention").classes("text-h5 font-bold")
        
        # Description row - left-aligned with table
        with ui.row().classes('mb-4 w-full justify-start px-4'):
            ui.label("Contracts approaching or past their expiration date").classes(
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
        
        # Search input for filtering contracts (above the table) - left-aligned with table
        with ui.row().classes('w-full mb-6 gap-2 justify-start px-4'):
            search_input = ui.input(placeholder='Search by Contract ID, Vendor, Type, Description, or Manager...').classes(
                'flex-1'
            ).props('outlined dense clearable')
            with search_input.add_slot('prepend'):
                ui.icon('search').classes('text-gray-400')
            ui.button(icon='search', on_click=filter_contracts).props('color=primary')
            ui.button(icon='clear', on_click=clear_search).props('color=secondary')
        
        # Create table after search bar (showing all contracts) - left-aligned with header
        initial_rows = contract_rows
        with ui.element("div").classes("w-full px-4"):
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
        
        # Add custom CSS for visual highlighting of expired contracts and toggle styling
        ui.add_css("""
            .contracts-table thead tr {
                background-color: #144c8e !important;
            }
            .contracts-table tbody tr:has(td:contains("Termination Pending")) {
                background-color: #fed7aa !important;
            }
            .contracts-table tbody tr:has(td:contains("past due")) {
                background-color: #fee2e2 !important;
            }
            .contracts-table tbody tr:has(td:contains("remaining")) {
                background-color: #fef3c7 !important;
            }
        """)
        
        # Add slot for contract ID with clickable link
        contracts_table.add_slot('body-cell-contract_id', '''
            <q-td :props="props">
                <a v-if="props.row.id" :href="'/contract-info/' + props.row.id" class="text-blue-600 hover:text-blue-800 underline cursor-pointer font-semibold">
                    {{ props.value }}
                </a>
                <span v-else class="text-gray-600">{{ props.value }}</span>
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

        # Contract Decision Dialog (same as pending_contracts.py)
        selected_contract = {}
        with ui.dialog().props("max-width=640px") as contract_decision_dialog, ui.card().classes("w-full max-w-3xl max-h-[90vh] overflow-y-auto p-6"):
            ui.label("Contract Decision").classes("text-h5 mb-4 text-blue-600 font-bold")
            dialog_content = ui.column().classes("w-full gap-4")

        def populate_contract_decision_dialog():
            dialog_content.clear()
            contract_db_id = selected_contract.get("contract_db_id") or selected_contract.get("id")
            contract_obj = None
            update = None
            acted_by_name = "N/A"
            existing_comments = ""
            try:
                db2 = SessionLocal()
                try:
                    contract_obj = (
                        db2.query(Contract)
                        .options(
                            joinedload(Contract.documents),
                            joinedload(Contract.termination_documents),
                            joinedload(Contract.contract_owner),
                            joinedload(Contract.contract_owner_backup),
                            joinedload(Contract.contract_owner_manager),
                        )
                        .filter(Contract.id == contract_db_id)
                        .first()
                    )
                    if contract_obj:
                        owner_name = f"{contract_obj.contract_owner.first_name} {contract_obj.contract_owner.last_name}" if contract_obj.contract_owner else "N/A"
                        backup_name = f"{contract_obj.contract_owner_backup.first_name} {contract_obj.contract_owner_backup.last_name}" if contract_obj.contract_owner_backup else "N/A"
                        manager_name = f"{contract_obj.contract_owner_manager.first_name} {contract_obj.contract_owner_manager.last_name}" if contract_obj.contract_owner_manager else "N/A"
                        acted_by_name = f"Contract Manager: {owner_name}, Backup: {backup_name}, Owner: {manager_name}"
                    update = (
                        db2.query(ContractUpdate)
                        .filter(ContractUpdate.contract_id == contract_db_id)
                        .order_by(ContractUpdate.created_at.desc())
                        .first()
                    )
                    if update and update.response_provided_by_user_id:
                        acted_user = db2.query(User).filter(User.id == update.response_provided_by_user_id).first()
                        if acted_user:
                            acted_by_name = f"{acted_user.first_name} {acted_user.last_name}"
                    if update and getattr(update, "decision_comments", None):
                        existing_comments = update.decision_comments or ""
                    prev_decision = (update.decision if update and update.decision else None) or selected_contract.get("decision") or "Terminate"
                    if prev_decision == "Extend":
                        prev_decision = "Renew"
                finally:
                    db2.close()
            except Exception as e:
                print(f"Error loading contract for dialog: {e}")
                prev_decision = "Terminate"

            status_label = selected_contract.get("status", "Requiring attention")
            status_color = "red" if "past due" in str(status_label).lower() else "orange"
            end_date_default = selected_contract.get("expiration_date") or ""
            if update and getattr(update, "initial_expiration_date", None):
                end_date_default = str(update.initial_expiration_date).replace("/", "-") if update.initial_expiration_date else end_date_default

            with dialog_content:
                # Display Status within the pop-up (same as pending_contracts)
                with ui.row().classes("mb-2 items-center gap-2"):
                    ui.label("Status:").classes("text-sm font-medium text-gray-600")
                    ui.badge(status_label, color=status_color).classes("text-sm font-semibold")

                # Contract summary
                with ui.row().classes("mb-4 p-4 bg-gray-50 rounded-lg w-full"):
                    with ui.column().classes("gap-1"):
                        ui.label(f"Contract ID: {selected_contract.get('contract_id', 'N/A')}").classes("font-bold text-lg")
                        ui.label(f"Vendor: {selected_contract.get('vendor_name', 'N/A')}").classes("text-gray-600")
                        ui.label(f"Expiration Date: {selected_contract.get('expiration_date', 'N/A')}").classes("text-gray-600")
                        ui.label(f"Action taken by: {acted_by_name}").classes("text-gray-600 text-sm")

                # Decision section
                ui.label("Decision").classes("text-lg font-bold")
                decision_options = ["Terminate", "Renew"]
                decision_select = ui.select(
                    options=decision_options,
                    value=prev_decision if prev_decision in decision_options else "Terminate"
                ).classes("w-full").props("outlined dense")

                end_date_container = ui.column().classes("w-full")
                with end_date_container:
                    end_date_input = ui.input("End Date (required for Renew)", value=end_date_default).props("type=date outlined dense").classes("w-full")

                term_doc_container = ui.column().classes("w-full")
                with term_doc_container:
                    ui.label("Termination Document (required for Terminate). Upload below if missing.").classes("text-sm font-medium")
                    term_doc_upload_ref = {"name": None, "content": None}
                    term_doc_name_input = ui.input("Document name", placeholder="e.g. Termination letter").props("outlined dense").classes("w-full")
                    term_doc_date_input = ui.input("Issue Date", value="").props("type=date outlined dense").classes("w-full")

                    async def on_term_file_upload(e):
                        term_doc_upload_ref["name"] = e.file.name
                        term_doc_upload_ref["content"] = await e.file.read()
                        set_complete_state()

                    ui.upload(on_upload=on_term_file_upload, auto_upload=True, label="Upload PDF (required for Terminate)").props("accept=.pdf outlined dense").classes("w-full")

                def toggle_decision_requirements():
                    if decision_select.value == "Renew":
                        end_date_container.visible = True
                        term_doc_container.visible = False
                    else:
                        end_date_container.visible = False
                        term_doc_container.visible = True

                decision_select.on_value_change(lambda e: toggle_decision_requirements())
                toggle_decision_requirements()

                # Documents & Comments
                ui.label("Documents & Comments").classes("text-lg font-bold mt-2")
                with ui.card().classes("p-4 bg-white border w-full"):
                    ui.label("Comments (Contract Manager / Backup / Owner can add comments below):").classes("font-medium")
                    comments_input = ui.textarea(value=existing_comments).classes("w-full").props("outlined readonly")
                    ui.separator()
                    ui.label("Contract documents:").classes("font-medium mt-2")
                    if contract_obj and contract_obj.documents:
                        for doc in contract_obj.documents:
                            with ui.row().classes("items-center justify-between w-full gap-2 py-1"):
                                ui.label(doc.custom_document_name or doc.file_name).classes("text-sm")
                                doc_date_str = doc.document_signed_date.strftime("%Y-%m-%d") if getattr(doc.document_signed_date, "strftime", None) else str(doc.document_signed_date)
                                ui.label(f"Issue date: {doc_date_str}").classes("text-xs text-gray-500")
                                ui.button("Download", icon="download", on_click=lambda p=doc.file_path, n=doc.file_name: ui.download(p, filename=n)).props("flat color=primary size=sm")
                    else:
                        ui.label("No contract documents uploaded.").classes("text-gray-500 italic")
                    ui.label("Termination documents:").classes("font-medium mt-2")
                    if contract_obj and contract_obj.termination_documents:
                        for tdoc in contract_obj.termination_documents:
                            with ui.row().classes("items-center justify-between w-full gap-2 py-1"):
                                ui.label(tdoc.document_name).classes("text-sm")
                                tdate_str = tdoc.document_date.strftime("%Y-%m-%d") if getattr(tdoc.document_date, "strftime", None) else str(tdoc.document_date)
                                ui.label(f"Document date: {tdate_str}").classes("text-xs text-gray-500")
                                ui.button("Download", icon="download", on_click=lambda p=tdoc.file_path, n=tdoc.file_name: ui.download(p, filename=n)).props("flat color=primary size=sm")
                    else:
                        ui.label("No termination documents yet. Upload above when Decision is Terminate.").classes("text-gray-500 italic")

                # Admin remarks (admin-specific)
                ui.label("Contract Admin Remarks (optional)").classes("font-medium mt-2")
                admin_remarks = ui.textarea(value=(update.admin_comments if update and update.admin_comments else "")).classes("w-full").props("outlined")

                # Complete, Save, Cancel (admin-specific)
                with ui.row().classes("gap-3 justify-end mt-4 w-full"):
                    complete_btn = ui.button("Complete", icon="check_circle").props("color=positive")
                    save_btn = ui.button("Save", icon="save").props("color=primary")
                    ui.button("Cancel", icon="cancel", on_click=contract_decision_dialog.close).props("flat color=grey")

                def can_complete():
                    if decision_select.value == "Renew":
                        return bool((end_date_input.value or "").strip())
                    has_existing = contract_obj and contract_obj.termination_documents and len(contract_obj.termination_documents) > 0
                    has_upload = term_doc_upload_ref.get("content")
                    return has_existing or bool(has_upload)

                def set_complete_state():
                    if can_complete():
                        complete_btn.props(remove="color=grey")
                        complete_btn.props("color=positive")
                    else:
                        complete_btn.props(remove="color=positive")
                        complete_btn.props("color=grey")

                def do_complete():
                    nonlocal contract_rows
                    if decision_select.value == "Renew" and not can_complete():
                        ui.notify("End date is required for Renew.", type="negative")
                        return
                    if decision_select.value == "Terminate" and not can_complete():
                        ui.notify("Please upload the Termination Document", type="negative")
                        return
                    try:
                        current_user_id = app.storage.user.get("user_id") if app.storage.user else None
                        db3 = SessionLocal()
                        try:
                            upd = (
                                db3.query(ContractUpdate)
                                .filter(ContractUpdate.contract_id == contract_db_id)
                                .order_by(ContractUpdate.created_at.desc())
                                .first()
                            )
                            if not upd:
                                upd = ContractUpdate(contract_id=contract_db_id, status=ContractUpdateStatus.PENDING_REVIEW)
                                db3.add(upd)
                            decision_value = decision_select.value
                            # Send to Pending Reviews: do NOT update contract end_date or status here.
                            # Admin will complete the review from Pending Reviews and then the contract is updated.
                            upd.status = ContractUpdateStatus.PENDING_REVIEW
                            upd.response_provided_by_user_id = current_user_id
                            upd.response_date = datetime.utcnow()
                            upd.decision = "Extend" if decision_value == "Renew" else "Terminate"
                            upd.decision_comments = (comments_input.value or "").strip() if getattr(comments_input, "value", None) is not None else ""
                            upd.admin_comments = admin_remarks.value
                            if decision_value == "Renew":
                                end_val = (end_date_input.value or "").strip()
                                if end_val:
                                    end_val = end_val.replace("/", "-")
                                    upd.initial_expiration_date = datetime.strptime(end_val, "%Y-%m-%d").date()
                                upd.has_document = False
                            else:
                                has_upload = term_doc_upload_ref.get("content")
                                if has_upload:
                                    import httpx
                                    tname = (term_doc_name_input.value or "").strip()
                                    tdate = (term_doc_date_input.value or "").strip()
                                    if tname and tdate:
                                        with httpx.Client(timeout=30.0) as client:
                                            client.post(
                                                f"http://localhost:8000/api/v1/contracts/{contract_db_id}/termination-documents",
                                                data={"document_name": tname, "document_date": tdate},
                                                files={"file": (term_doc_upload_ref["name"] or "document.pdf", term_doc_upload_ref["content"], "application/pdf")},
                                            )
                                upd.has_document = bool(has_upload)
                            upd.updated_at = datetime.utcnow()
                            db3.commit()
                            ui.notify("Contract sent to Pending Reviews. Complete the review there to apply the decision.", type="positive")
                            contract_rows = get_contracts_requiring_attention()
                            contracts_table.rows = contract_rows
                            contracts_table.update()
                        finally:
                            db3.close()
                    except Exception as e:
                        ui.notify(f"Error sending to Pending Reviews: {e}", type="negative")
                    contract_decision_dialog.close()

                def do_save():
                    """Save progress without completing or returning."""
                    nonlocal contract_rows
                    try:
                        db3 = SessionLocal()
                        try:
                            upd = (
                                db3.query(ContractUpdate)
                                .filter(ContractUpdate.contract_id == contract_db_id)
                                .order_by(ContractUpdate.created_at.desc())
                                .first()
                            )
                            if not upd:
                                upd = ContractUpdate(contract_id=contract_db_id, status=ContractUpdateStatus.PENDING_REVIEW)
                                db3.add(upd)
                            upd.decision = "Extend" if decision_select.value == "Renew" else "Terminate"
                            comments = (admin_remarks.value or "").strip()
                            if decision_select.value == "Terminate":
                                tname = (term_doc_name_input.value or "").strip()
                                tdate = (term_doc_date_input.value or "").strip()
                                if tname or tdate:
                                    comments = (comments + "\n" if comments else "") + f"[Planned termination doc: {tname or '(not set)'}, date: {tdate or '(not set)'}]"
                            upd.decision_comments = comments
                            upd.admin_comments = admin_remarks.value
                            if decision_select.value == "Renew":
                                end_val = (end_date_input.value or "").strip()
                                if end_val:
                                    upd.initial_expiration_date = datetime.strptime(end_val.replace("/", "-"), "%Y-%m-%d").date()
                            upd.updated_at = datetime.utcnow()
                            db3.commit()
                            ui.notify("Progress saved", type="positive")
                            contract_rows = get_contracts_requiring_attention()
                            contracts_table.rows = contract_rows
                            contracts_table.update()
                        finally:
                            db3.close()
                    except Exception as e:
                        ui.notify(f"Error saving: {e}", type="negative")
                    contract_decision_dialog.close()

                complete_btn.on_click(do_complete)
                save_btn.on_click(do_save)
                set_complete_state()
                decision_select.on_value_change(lambda e: set_complete_state())
                end_date_input.on_value_change(lambda e: set_complete_state())
                term_doc_name_input.on_value_change(lambda e: set_complete_state())
                term_doc_date_input.on_value_change(lambda e: set_complete_state())

        def open_contract_decision_dialog(row: dict):
            selected_contract.clear()
            selected_contract["contract_id"] = row.get("contract_id", "")
            selected_contract["contract_db_id"] = row.get("id", 0)
            selected_contract["vendor_name"] = row.get("vendor_name", "N/A")
            selected_contract["expiration_date"] = row.get("expiration_date", "N/A")
            selected_contract["status"] = row.get("status", "N/A")
            selected_contract["decision"] = row.get("decision")
            populate_contract_decision_dialog()
            contract_decision_dialog.open()

        def on_status_click(e):
            try:
                row = e.args
                if isinstance(row, dict) and row.get("id") is not None:
                    open_contract_decision_dialog(row)
            except Exception as ex:
                ui.notify(f"Could not open Contract Decision dialog: {ex}", type="negative")

        contracts_table.on("status_click", on_status_click)

        # Add slot for status column - clickable to open Contract Decision modal
        contracts_table.add_slot('body-cell-status', '''
            <q-td :props="props">
                <q-btn
                    flat
                    no-caps
                    dense
                    :icon="props.value.includes('past due') ? 'error' : 'warning'"
                    :color="props.value.includes('past due') ? 'red' : 'orange'"
                    :label="props.value"
                    class="font-semibold cursor-pointer"
                    style="text-transform:none;"
                    @click="$parent.$emit('status_click', props.row)"
                />
            </q-td>
        ''')
