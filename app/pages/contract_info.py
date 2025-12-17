from nicegui import ui
from datetime import datetime, date
from app.models.contract import (
    ContractType, AutomaticRenewalType, RenewalPeriodType, DepartmentType,
    NoticePeriodType, ExpirationNoticePeriodType, CurrencyType, PaymentMethodType,
    ContractStatusType, ContractTerminationType
)


def contract_info(contract_id: int):
    """Display contract information by ID"""
    # Fetch contract from database
    from app.db.database import SessionLocal
    from sqlalchemy.orm import joinedload
    
    contract = None
    db = SessionLocal()
    try:
        from app.models.contract import Contract
        contract = db.query(Contract).options(
            joinedload(Contract.vendor),
            joinedload(Contract.contract_owner),
            joinedload(Contract.contract_owner_backup),
            joinedload(Contract.contract_owner_manager),
            joinedload(Contract.documents)
        ).filter(Contract.id == contract_id).first()
        
        if not contract:
            print(f"Contract with ID {contract_id} not found")
    except Exception as e:
        print(f"Error loading contract data: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
    
    # Navigation
    with ui.row().classes("max-w-5xl mx-auto mt-4"):
        if contract and contract.vendor:
            with ui.link(target=f'/vendor-contracts/{contract.vendor_id}').classes('no-underline'):
                ui.button("Back to Vendor Contracts", icon="arrow_back").props('flat color=primary')
    
    # Basic info
    with ui.card().classes("w-full max-w-5xl mx-auto mt-4 p-6"):
        with ui.row().classes("items-center justify-between mb-4 w-full"):
            ui.label("Contract Info").classes("text-h5")
            if contract:
                with ui.row().classes("gap-2"):
                    # Edit icon button
                    edit_btn = ui.button(icon="edit", on_click=lambda: open_edit_dialog()).props('flat color=primary')
                    edit_btn.tooltip('Edit Contract')
        
        if not contract:
            ui.label("No contract selected. Please select a contract from the contracts list.").classes("text-red-600")
        else:
            # Contract ID and Vendor
            with ui.row().classes("mb-2 gap-4"):
                ui.label(f"Contract ID: {contract.contract_id}").classes("font-bold")
                ui.label(f"Vendor: {contract.vendor.vendor_name}").classes("font-bold")
            
            # Description and Type
            with ui.row().classes("mb-2 gap-4"):
                ui.label(f"Description: {contract.contract_description}")
                ui.label(f"Type: {contract.contract_type.value}")
            
            # Status and Dates
            with ui.row().classes("mb-2 items-center gap-4"):
                with ui.row().classes("items-center gap-2"):
                    ui.label("Status:").classes("text-lg font-bold")
                    # Status coloring: Active=green, Expired=red, Terminated=black, Pending Termination=orange
                    if contract.status.value == "Active":
                        status_color = "green"
                    elif contract.status.value == "Expired":
                        status_color = "red"
                    elif contract.status.value == "Terminated":
                        status_color = "black"
                    elif contract.status.value == "Pending Termination":
                        status_color = "orange"
                    else:
                        status_color = "gray"
                    ui.badge(contract.status.value, color=status_color).classes("text-sm font-semibold")
                ui.label(f"Start Date: {contract.start_date.strftime('%Y-%m-%d')}")
                ui.label(f"End Date: {contract.end_date.strftime('%Y-%m-%d')}")
            
            # Department and Financial
            with ui.row().classes("mb-2 gap-4"):
                ui.label(f"Department: {contract.department.value}")
                ui.label(f"Amount: {contract.contract_currency.value} {contract.contract_amount}")
                ui.label(f"Payment Method: {contract.payment_method.value}")
            
            # Contract Ownership
            with ui.row().classes("mb-2 gap-4"):
                owner_name = f"{contract.contract_owner.first_name} {contract.contract_owner.last_name}" if contract.contract_owner else "N/A"
                backup_name = f"{contract.contract_owner_backup.first_name} {contract.contract_owner_backup.last_name}" if contract.contract_owner_backup else "N/A"
                manager_name = f"{contract.contract_owner_manager.first_name} {contract.contract_owner_manager.last_name}" if contract.contract_owner_manager else "N/A"
                ui.label(f"Owner: {owner_name}")
                ui.label(f"Backup: {backup_name}")
                ui.label(f"Manager: {manager_name}")
            
            # Renewal Information
            with ui.row().classes("mb-2 gap-4"):
                ui.label(f"Automatic Renewal: {contract.automatic_renewal.value}")
                if contract.renewal_period:
                    ui.label(f"Renewal Period: {contract.renewal_period.value}")
            
            # Notice Periods
            with ui.row().classes("mb-2 gap-4"):
                ui.label(f"Termination Notice Period: {contract.termination_notice_period.value}")
                ui.label(f"Expiration Notice Frequency: {contract.expiration_notice_frequency.value}")
    
    # Edit Contract Dialog
    if contract:
        # Get all users for dropdowns
        db = SessionLocal()
        try:
            from app.models.contract import User
            all_users = db.query(User).filter(User.is_active == True).all()
        finally:
            db.close()
        
        # Create edit dialog with all contract fields
        with ui.dialog() as edit_dialog, ui.card().classes("min-w-[900px] max-w-5xl max-h-[90vh] overflow-y-auto"):
            ui.label("Edit Contract").classes("text-h5 mb-4 text-blue-600 font-bold")
            
            # Store original values for change tracking
            original_values = {}
            edited_fields = {}
            
            # Track if any changes were made
            has_changes_ref = {'value': False}
            
            with ui.column().classes("w-full gap-4"):
                # Contract ID (Read-only)
                with ui.row().classes("w-full gap-4"):
                    ui.input(label="Contract ID", value=contract.contract_id).classes("flex-1").props('outlined readonly')
                
                # Vendor (Read-only)
                with ui.row().classes("w-full gap-4"):
                    ui.input(label="Vendor", value=contract.vendor.vendor_name).classes("flex-1").props('outlined readonly')
                
                # Description
                with ui.row().classes("w-full gap-4"):
                    description_input = ui.input(label="Contract Description *", value=contract.contract_description).classes("flex-1").props('outlined')
                    original_values['contract_description'] = contract.contract_description
                
                # Contract Type
                contract_types = [ct.value for ct in ContractType]
                with ui.row().classes("w-full gap-4"):
                    contract_type_select = ui.select(
                        label="Contract Type *",
                        options=contract_types,
                        value=contract.contract_type.value
                    ).classes("flex-1").props('outlined')
                    original_values['contract_type'] = contract.contract_type.value
                
                # Dates
                start_date_val = contract.start_date.strftime("%Y-%m-%d") if contract.start_date else ""
                end_date_val = contract.end_date.strftime("%Y-%m-%d") if contract.end_date else ""
                
                with ui.row().classes("w-full gap-4"):
                    start_date_input = ui.input(label="Start Date *", value=start_date_val).classes("flex-1").props('outlined type=date')
                    end_date_input = ui.input(label="End Date *", value=end_date_val).classes("flex-1").props('outlined type=date')
                    original_values['start_date'] = start_date_val
                    original_values['end_date'] = end_date_val
                
                # Contract Status (can be updated at any point in contract lifecycle)
                # All 4 status options available for manual selection
                status_options = ["Active", "Expired", "Terminated", "Pending Termination"]
                with ui.row().classes("w-full gap-4"):
                    status_select = ui.select(
                        label="Contract Status *",
                        options=status_options,
                        value=contract.status.value
                    ).classes("flex-1").props('outlined')
                    original_values['status'] = contract.status.value
                
                # Status update note
                with ui.row().classes("w-full"):
                    ui.label("Note: Updating the contract status will immediately reflect the new state upon saving.").classes("text-xs text-gray-500 italic")
                
                # Department
                department_options = [d.value for d in DepartmentType]
                with ui.row().classes("w-full gap-4"):
                    department_select = ui.select(
                        label="Department *",
                        options=department_options,
                        value=contract.department.value
                    ).classes("flex-1").props('outlined')
                    original_values['department'] = contract.department.value
                
                # Financial Information
                with ui.row().classes("w-full gap-4"):
                    amount_input = ui.input(label="Contract Amount *", value=str(contract.contract_amount)).classes("flex-1").props('outlined type=number')
                    original_values['contract_amount'] = str(contract.contract_amount)
                
                currency_options = [c.value for c in CurrencyType]
                payment_method_options = [pm.value for pm in PaymentMethodType]
                
                with ui.row().classes("w-full gap-4"):
                    currency_select = ui.select(
                        label="Currency *",
                        options=currency_options,
                        value=contract.contract_currency.value
                    ).classes("flex-1").props('outlined')
                    payment_method_select = ui.select(
                        label="Payment Method *",
                        options=payment_method_options,
                        value=contract.payment_method.value
                    ).classes("flex-1").props('outlined')
                    original_values['currency'] = contract.contract_currency.value
                    original_values['payment_method'] = contract.payment_method.value
                
                # Automatic Renewal
                renewal_options = [r.value for r in AutomaticRenewalType]
                renewal_period_options = [rp.value for rp in RenewalPeriodType]
                
                with ui.row().classes("w-full gap-4"):
                    automatic_renewal_select = ui.select(
                        label="Automatic Renewal *",
                        options=renewal_options,
                        value=contract.automatic_renewal.value
                    ).classes("flex-1").props('outlined')
                    renewal_period_select = ui.select(
                        label="Renewal Period",
                        options=renewal_period_options,
                        value=contract.renewal_period.value if contract.renewal_period else None
                    ).classes("flex-1").props('outlined')
                    original_values['automatic_renewal'] = contract.automatic_renewal.value
                    original_values['renewal_period'] = contract.renewal_period.value if contract.renewal_period else ""
                
                # Notice Periods
                notice_period_options = [np.value for np in NoticePeriodType]
                expiration_notice_options = [en.value for en in ExpirationNoticePeriodType]
                
                with ui.row().classes("w-full gap-4"):
                    termination_notice_select = ui.select(
                        label="Termination Notice Period *",
                        options=notice_period_options,
                        value=contract.termination_notice_period.value
                    ).classes("flex-1").props('outlined')
                    expiration_notice_select = ui.select(
                        label="Expiration Notice Frequency *",
                        options=expiration_notice_options,
                        value=contract.expiration_notice_frequency.value
                    ).classes("flex-1").props('outlined')
                    original_values['termination_notice_period'] = contract.termination_notice_period.value
                    original_values['expiration_notice_frequency'] = contract.expiration_notice_frequency.value
                
                # Contract Owners
                user_options = [f"{u.first_name} {u.last_name} ({u.email})" for u in all_users]
                user_id_map = {f"{u.first_name} {u.last_name} ({u.email})": u.id for u in all_users}
                
                current_owner = f"{contract.contract_owner.first_name} {contract.contract_owner.last_name} ({contract.contract_owner.email})" if contract.contract_owner else None
                current_backup = f"{contract.contract_owner_backup.first_name} {contract.contract_owner_backup.last_name} ({contract.contract_owner_backup.email})" if contract.contract_owner_backup else None
                current_manager = f"{contract.contract_owner_manager.first_name} {contract.contract_owner_manager.last_name} ({contract.contract_owner_manager.email})" if contract.contract_owner_manager else None
                
                with ui.row().classes("w-full gap-4"):
                    owner_select = ui.select(
                        label="Contract Owner *",
                        options=user_options,
                        value=current_owner
                    ).classes("flex-1").props('outlined')
                    original_values['contract_owner_id'] = contract.contract_owner_id
                
                with ui.row().classes("w-full gap-4"):
                    backup_select = ui.select(
                        label="Contract Owner Backup *",
                        options=user_options,
                        value=current_backup
                    ).classes("flex-1").props('outlined')
                    original_values['contract_owner_backup_id'] = contract.contract_owner_backup_id
                
                with ui.row().classes("w-full gap-4"):
                    manager_select = ui.select(
                        label="Contract Owner Manager *",
                        options=user_options,
                        value=current_manager
                    ).classes("flex-1").props('outlined')
                    original_values['contract_owner_manager_id'] = contract.contract_owner_manager_id
                
                # Contract Termination
                termination_options = [t.value for t in ContractTerminationType]
                with ui.row().classes("w-full gap-4"):
                    termination_select = ui.select(
                        label="Contract Termination",
                        options=termination_options,
                        value=contract.contract_termination.value if contract.contract_termination else None
                    ).classes("flex-1").props('outlined')
                    original_values['contract_termination'] = contract.contract_termination.value if contract.contract_termination else ""
                
                # Function to check if any field changed
                def check_changes():
                    changes = {}
                    if description_input.value != original_values['contract_description']:
                        changes['contract_description'] = description_input.value
                    if contract_type_select.value != original_values['contract_type']:
                        changes['contract_type'] = contract_type_select.value
                    if start_date_input.value != original_values['start_date']:
                        changes['start_date'] = start_date_input.value
                    if end_date_input.value != original_values['end_date']:
                        changes['end_date'] = end_date_input.value
                    if status_select.value != original_values['status']:
                        changes['status'] = status_select.value
                    if department_select.value != original_values['department']:
                        changes['department'] = department_select.value
                    if amount_input.value != original_values['contract_amount']:
                        changes['contract_amount'] = amount_input.value
                    if currency_select.value != original_values['currency']:
                        changes['currency'] = currency_select.value
                    if payment_method_select.value != original_values['payment_method']:
                        changes['payment_method'] = payment_method_select.value
                    if automatic_renewal_select.value != original_values['automatic_renewal']:
                        changes['automatic_renewal'] = automatic_renewal_select.value
                    if (renewal_period_select.value or "") != original_values['renewal_period']:
                        changes['renewal_period'] = renewal_period_select.value
                    if termination_notice_select.value != original_values['termination_notice_period']:
                        changes['termination_notice_period'] = termination_notice_select.value
                    if expiration_notice_select.value != original_values['expiration_notice_frequency']:
                        changes['expiration_notice_frequency'] = expiration_notice_select.value
                    if (termination_select.value or "") != original_values['contract_termination']:
                        changes['contract_termination'] = termination_select.value
                    
                    # Check owner changes
                    if owner_select.value and user_id_map.get(owner_select.value) != original_values['contract_owner_id']:
                        changes['contract_owner_id'] = user_id_map.get(owner_select.value)
                    if backup_select.value and user_id_map.get(backup_select.value) != original_values['contract_owner_backup_id']:
                        changes['contract_owner_backup_id'] = user_id_map.get(backup_select.value)
                    if manager_select.value and user_id_map.get(manager_select.value) != original_values['contract_owner_manager_id']:
                        changes['contract_owner_manager_id'] = user_id_map.get(manager_select.value)
                    
                    has_changes = len(changes) > 0
                    has_changes_ref['value'] = has_changes
                    edited_fields.clear()
                    edited_fields.update(changes)
                    save_btn.set_enabled(has_changes)
                    return has_changes
                
                # Attach change handlers to all inputs
                description_input.on('blur', check_changes)
                contract_type_select.on('update:model-value', check_changes)
                start_date_input.on('blur', check_changes)
                end_date_input.on('blur', check_changes)
                status_select.on('update:model-value', check_changes)
                department_select.on('update:model-value', check_changes)
                amount_input.on('blur', check_changes)
                currency_select.on('update:model-value', check_changes)
                payment_method_select.on('update:model-value', check_changes)
                automatic_renewal_select.on('update:model-value', check_changes)
                renewal_period_select.on('update:model-value', check_changes)
                termination_notice_select.on('update:model-value', check_changes)
                expiration_notice_select.on('update:model-value', check_changes)
                termination_select.on('update:model-value', check_changes)
                owner_select.on('update:model-value', check_changes)
                backup_select.on('update:model-value', check_changes)
                manager_select.on('update:model-value', check_changes)
                
                # Action buttons
                with ui.row().classes("gap-4 mt-6 w-full justify-end"):
                    ui.button("Cancel", icon="cancel", on_click=lambda: close_edit_dialog()).props('flat color=grey')
                    save_btn = ui.button("Save Changes", icon="save", on_click=lambda: save_contract_changes()).props('color=primary')
                    save_btn.set_enabled(False)  # Initially disabled
        
        # Function to open edit dialog
        def open_edit_dialog():
            # Reset changes tracking
            has_changes_ref['value'] = False
            edited_fields.clear()
            save_btn.set_enabled(False)
            edit_dialog.open()
        
        # Function to close edit dialog with confirmation if changes exist
        def close_edit_dialog():
            if has_changes_ref['value']:
                # Show confirmation dialog
                with ui.dialog() as confirm_dialog, ui.card():
                    ui.label("Unsaved Changes").classes("text-h6 mb-4")
                    ui.label("You have unsaved changes. What would you like to do?").classes("mb-4")
                    
                    with ui.row().classes("gap-2 w-full justify-end"):
                        ui.button("Cancel", on_click=confirm_dialog.close).props('flat')
                        ui.button("Discard Changes", on_click=lambda: [confirm_dialog.close(), edit_dialog.close()]).props('color=orange')
                        ui.button("Save Changes", on_click=lambda: [confirm_dialog.close(), save_contract_changes()]).props('color=primary')
                
                confirm_dialog.open()
            else:
                edit_dialog.close()
        
        # Function to save contract changes
        async def save_contract_changes():
            import httpx
            
            if not has_changes_ref['value']:
                ui.notify("No changes to save", type="info")
                return
            
            # Get current user from app storage
            from nicegui import app
            current_user = app.storage.user.get('username', 'SYSTEM')
            
            # Prepare update data (only changed fields)
            update_data = {}
            
            # Map UI fields to API fields
            if 'contract_description' in edited_fields:
                update_data['contract_description'] = description_input.value
            if 'contract_type' in edited_fields:
                update_data['contract_type'] = contract_type_select.value
            if 'start_date' in edited_fields:
                update_data['start_date'] = start_date_input.value
            if 'end_date' in edited_fields:
                update_data['end_date'] = end_date_input.value
            if 'status' in edited_fields:
                update_data['status'] = status_select.value
            if 'department' in edited_fields:
                update_data['department'] = department_select.value
            if 'contract_amount' in edited_fields:
                update_data['contract_amount'] = float(amount_input.value)
            if 'currency' in edited_fields:
                update_data['contract_currency'] = currency_select.value
            if 'payment_method' in edited_fields:
                update_data['payment_method'] = payment_method_select.value
            if 'automatic_renewal' in edited_fields:
                update_data['automatic_renewal'] = automatic_renewal_select.value
            if 'renewal_period' in edited_fields:
                update_data['renewal_period'] = renewal_period_select.value if renewal_period_select.value else None
            if 'termination_notice_period' in edited_fields:
                update_data['termination_notice_period'] = termination_notice_select.value
            if 'expiration_notice_frequency' in edited_fields:
                update_data['expiration_notice_frequency'] = expiration_notice_select.value
            if 'contract_termination' in edited_fields:
                update_data['contract_termination'] = termination_select.value if termination_select.value else None
            if 'contract_owner_id' in edited_fields:
                update_data['contract_owner_id'] = edited_fields['contract_owner_id']
            if 'contract_owner_backup_id' in edited_fields:
                update_data['contract_owner_backup_id'] = edited_fields['contract_owner_backup_id']
            if 'contract_owner_manager_id' in edited_fields:
                update_data['contract_owner_manager_id'] = edited_fields['contract_owner_manager_id']
            
            # Call API to update contract
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.put(
                        f"http://localhost:8000/api/v1/contracts/{contract.id}?modified_by={current_user}",
                        json=update_data,
                        headers={"Content-Type": "application/json"}
                    )
                    
                    if response.status_code == 200:
                        # Check if status was updated
                        if 'status' in edited_fields:
                            ui.notify(f"Contract updated successfully! Status changed to: {status_select.value}", type="positive")
                        else:
                            ui.notify("Contract updated successfully!", type="positive")
                        edit_dialog.close()
                        # Reload the page to show updated data
                        ui.navigate.reload()
                    else:
                        error_detail = response.json().get('detail', 'Unknown error')
                        ui.notify(f"Failed to update contract: {error_detail}", type="negative")
            except Exception as e:
                ui.notify(f"Error updating contract: {str(e)}", type="negative")
                print(f"Error updating contract: {e}")
                import traceback
                traceback.print_exc()
    
    # Display last modified info if available
    if contract and contract.last_modified_by:
        with ui.card().classes("w-full max-w-5xl mx-auto mt-4 p-4 bg-gray-50"):
            with ui.row().classes("items-center gap-2"):
                ui.icon("history", color="gray").classes("text-lg")
                last_modified_date = contract.last_modified_date.strftime("%Y-%m-%d %H:%M:%S") if contract.last_modified_date else "Unknown"
                ui.label(f"Last modified by {contract.last_modified_by} on {last_modified_date}").classes("text-sm text-gray-600")
    
    # Documents Section
    if contract:
        with ui.card().classes("w-full max-w-5xl mx-auto mt-6 p-6"):
            ui.label("Contract Documents").classes("text-h5 mb-4 text-blue-600 font-bold")
            
            if contract.documents:
                ui.badge(f"{len(contract.documents)} document(s)", color="green").classes("text-sm font-semibold mb-4")
                
                for doc in contract.documents:
                    with ui.row().classes("items-center gap-4 p-3 bg-gray-50 rounded-lg mb-2 w-full"):
                        with ui.column().classes("flex-1"):
                            ui.label(doc.custom_document_name).classes("font-medium text-gray-800")
                            signed_date = doc.document_signed_date.strftime("%Y-%m-%d") if doc.document_signed_date else "N/A"
                            ui.label(f"Signed Date: {signed_date}").classes("text-sm text-gray-600")
                        
                        # View/Download buttons
                        with ui.row().classes("gap-2"):
                            view_btn = ui.button("View", icon="visibility").props('color=primary flat size=sm')
                            download_btn = ui.button("Download", icon="download").props('color=secondary flat size=sm')
                            
                            def make_download_handler(doc_path, doc_name, file_name):
                                def download_document():
                                    import os
                                    if os.path.exists(doc_path):
                                        with open(doc_path, 'rb') as f:
                                            file_content = f.read()
                                        import base64
                                        b64_content = base64.b64encode(file_content).decode()
                                        ui.run_javascript(f'''
                                            const link = document.createElement('a');
                                            link.href = 'data:application/pdf;base64,{b64_content}';
                                            link.download = '{file_name}';
                                            document.body.appendChild(link);
                                            link.click();
                                            document.body.removeChild(link);
                                        ''')
                                        ui.notify(f"Downloaded {doc_name}", type="positive")
                                    else:
                                        ui.notify(f"File not found: {doc_name}", type="negative")
                                return download_document
                            
                            view_btn.on_click(make_download_handler(doc.file_path, doc.custom_document_name, doc.file_name))
                            download_btn.on_click(make_download_handler(doc.file_path, doc.custom_document_name, doc.file_name))
            else:
                ui.label("No documents uploaded").classes("text-gray-500 italic")

