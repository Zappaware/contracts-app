

from nicegui import ui
from datetime import datetime

def vendor_info():
    # Navigation
    with ui.row().classes("max-w-3xl mx-auto mt-4"):
        with ui.link(target='/').classes('no-underline'):
            ui.button("← Back to Dashboard", icon="arrow_back").props('flat color=primary')
    
    # Basic info
    with ui.card().classes("max-w-3xl mx-auto mt-4 p-6"):
        ui.label("Vendor Info").classes("text-h5 mb-4")
        with ui.row().classes("mb-2"):
            ui.label("Vendor ID: -").classes("font-bold")
            ui.label("Vendor Name: -").classes("font-bold")
        with ui.row().classes("mb-2"):
            ui.label("Status: -").classes("text-lg font-bold text-black-700")
            ui.label("Contact Person: -")
            ui.label("Email: -")
        with ui.row().classes("mb-2"):
            ui.label("Next Required Due Diligence Date: -")

        more = ui.button("More", icon="expand_more").props("flat")
        details_card = ui.card().classes("mt-4 hidden")

        def show_details():
            details_card.classes(remove="hidden")
        more.on("click", show_details)

        with details_card:
            ui.label("All Vendor Details").classes("text-h6 mb-2")
            with ui.row():
                ui.label("Address: -")
                ui.label("City: -")
                ui.label("Country: -")
            with ui.row():
                ui.label("Phone: -")
                ui.label("Bank Customer: -")
                ui.label("CIF: -")
            with ui.row():
                ui.label("Material Outsourcing Agreement: -")
                ui.label("Last Due Diligence Date: -")
                ui.label("Next Required Due Diligence Alert Frequency: -")
            ui.label("Due Diligence Info:").classes("mt-2 font-bold")
            ui.label("-")

    # Contract Termination Section
    with ui.card().classes("max-w-3xl mx-auto mt-6 p-6"):
        ui.label("Contract Termination Decision").classes("text-h5 mb-4 text-red-600")
        
        # Contract details
        with ui.row().classes("mb-4 p-4 bg-gray-50 rounded-lg"):
            with ui.column():
                ui.label("Contract ID: CTR-2024-001").classes("font-bold text-lg")
                ui.label("Vendor: Acme Corp").classes("text-gray-600")
                ui.label("Expiration Date: 2024-01-15").classes("text-gray-600")
                ui.label("Status: Expired (5 days past due)").classes("text-red-600 font-bold")
        
        # Termination decision form
        with ui.column().classes("space-y-4"):
            ui.label("Termination Decision").classes("text-lg font-bold")
            
            # Decision options
            with ui.row().classes("gap-4"):
                terminate_radio = ui.radio(['Terminate', 'Renew', 'Extend'], value='Terminate').props('inline')
            
            # Termination reason
            with ui.column().classes("w-full"):
                ui.label("Termination Reason (Optional)").classes("font-medium")
                termination_reason = ui.textarea(placeholder="Enter reason for termination...").classes("w-full").props('outlined')
            
            # Action buttons
            with ui.row().classes("gap-4 mt-6"):
                save_decision_btn = ui.button("Save Termination Decision", icon="save").props('color=red')
                cancel_btn = ui.button("Cancel", icon="cancel").props('color=grey')
                
                # Upload documents button (initially hidden)
                upload_docs_btn = ui.button("Upload Required Documents", icon="upload").props('color=primary')
                upload_docs_btn.visible = False
        
        # Status indicator
        status_indicator = ui.element("div").classes("mt-4 p-4 rounded-lg hidden")
        
        # Function to handle termination decision save
        def save_termination_decision():
            if terminate_radio.value == 'Terminate':
                # Save the termination decision
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Show success message
                status_indicator.classes(remove="hidden")
                status_indicator.classes("bg-green-100 border border-green-400 text-green-700")
                status_indicator.clear()
                with status_indicator:
                    ui.icon('check_circle', color='green').classes('text-2xl')
                    ui.label("Termination Decision Saved Successfully!").classes("ml-2 font-bold")
                    ui.label(f"Saved on: {current_time}").classes("ml-2 text-sm")
                    ui.label("Status: Termination Pending – Documents Required").classes("ml-2 text-sm font-bold text-orange-600")
                
                # Show upload documents button
                upload_docs_btn.visible = True
                
                # Hide the form
                terminate_radio.visible = False
                termination_reason.visible = False
                save_decision_btn.visible = False
                cancel_btn.visible = False
                
                ui.notify("Termination decision saved! Contract marked as 'Termination Pending – Documents Required'", type="positive")
            else:
                ui.notify("Please select 'Terminate' to save a termination decision", type="warning")
        
        # Function to handle cancel
        def cancel_termination():
            terminate_radio.value = 'Terminate'
            termination_reason.value = ""
            ui.notify("Termination decision cancelled", type="info")
        
        # Function to handle document upload
        def upload_documents():
            ui.notify("Document upload functionality will be implemented in the next phase", type="info")
        
        # Bind button events
        save_decision_btn.on_click(save_termination_decision)
        cancel_btn.on_click(cancel_termination)
        upload_docs_btn.on_click(upload_documents)
        
        # Instructions
        with ui.card().classes("mt-6 p-4 bg-blue-50 border-l-4 border-blue-400"):
            ui.label("Instructions:").classes("font-bold text-blue-800")
            ui.label("• Select 'Terminate' to save your termination decision").classes("text-blue-700")
            ui.label("• You can optionally provide a reason for termination").classes("text-blue-700")
            ui.label("• After saving, the contract will be marked as 'Termination Pending – Documents Required'").classes("text-blue-700")
            ui.label("• Required documents can be uploaded later from the Pending Documents for Termination workbasket").classes("text-blue-700")

    # Action Buttons Section
    with ui.card().classes("max-w-3xl mx-auto mt-6 p-6"):
        ui.label("Contract Actions").classes("text-h5 mb-4 text-blue-600")
        
        with ui.row().classes("gap-4 w-full justify-center"):
            # Contract Actions Button
            contract_actions_btn = ui.button("Contract Actions", icon="settings").props('color=primary size=lg')
            
            # Pending Documents Button
            pending_docs_btn = ui.button("Pending Documents", icon="upload").props('color=orange size=lg')
        
        # Contract Actions Dialog
        with ui.dialog() as contract_actions_dialog, ui.card().classes("w-96"):
            ui.label("Contract Actions").classes("text-h6 mb-4")
            
            # Action selection
            with ui.column().classes("space-y-4 w-full"):
                ui.label("Select Action:").classes("font-bold")
                action_radio = ui.radio(['Extend', 'Terminate'], value='Extend').props('inline')
                
                # Extend section
                with ui.column().classes("w-full") as extend_section:
                    ui.label("New Expiration Date (Required for Extension)").classes("font-medium")
                    new_expiry_date = ui.input(placeholder="YYYY-MM-DD").props('outlined dense')
                    ui.label("Example: 2024-12-31").classes("text-xs text-gray-500")
                
                # Terminate section
                with ui.column().classes("w-full") as terminate_section:
                    ui.label("Termination Document (Optional)").classes("font-medium")
                    termination_file = ui.upload(
                        on_upload=lambda e: ui.notify(f'Uploaded {e.name}'),
                        on_rejected=lambda e: ui.notify(f'Rejected {e}'),
                        max_file_size=10_000_000,  # 10MB
                        max_total_size=50_000_000,  # 50MB
                        max_files=5
                    ).classes('w-full')
                    ui.label("Upload PDF files only").classes("text-xs text-gray-500")
                
                # Action buttons
                with ui.row().classes("gap-2 mt-4 w-full justify-end"):
                    process_btn = ui.button("Process Action", icon="check").props('color=green')
                    cancel_actions_btn = ui.button("Cancel", icon="cancel").props('color=grey')
        
        # Pending Documents Dialog
        with ui.dialog() as pending_docs_dialog, ui.card().classes("w-96"):
            ui.label("Upload Pending Documents").classes("text-h6 mb-4")
            
            with ui.column().classes("space-y-4 w-full"):
                ui.label("Required Documents:").classes("font-bold")
                ui.label("• Contract Agreement").classes("text-sm")
                ui.label("• Vendor Registration Certificate").classes("text-sm")
                ui.label("• Insurance Certificate").classes("text-sm")
                ui.label("• Compliance Documentation").classes("text-sm")
                
                ui.separator()
                
                ui.label("Upload Documents:").classes("font-bold")
                pending_file_upload = ui.upload(
                    on_upload=lambda e: ui.notify(f'Uploaded {e.name}'),
                    on_rejected=lambda e: ui.notify(f'Rejected {e}'),
                    max_file_size=10_000_000,  # 10MB
                    max_total_size=100_000_000,  # 100MB
                    max_files=10
                ).classes('w-full')
                ui.label("Accepted formats: PDF, DOC, DOCX, JPG, PNG").classes("text-xs text-gray-500")
                
                # Upload buttons
                with ui.row().classes("gap-2 mt-4 w-full justify-end"):
                    upload_btn = ui.button("Upload Documents", icon="upload").props('color=primary')
                    cancel_upload_btn = ui.button("Cancel", icon="cancel").props('color=grey')
        
        # Dialog functions
        def open_contract_actions():
            contract_actions_dialog.open()
        
        def open_pending_docs():
            pending_docs_dialog.open()
        
        def process_contract_action():
            if action_radio.value == 'Extend':
                if not new_expiry_date.value:
                    ui.notify("New expiration date is required for extension", type="error")
                    return
                ui.notify(f"Contract extended to {new_expiry_date.value}", type="positive")
            else:  # Terminate
                if not termination_file.value:
                    ui.notify("Termination processed without documents", type="info")
                else:
                    ui.notify("Termination processed with documents", type="positive")
            contract_actions_dialog.close()
        
        def upload_pending_documents():
            if not pending_file_upload.value:
                ui.notify("No documents selected", type="warning")
                return
            ui.notify("Documents uploaded successfully", type="positive")
            pending_docs_dialog.close()
        
        def cancel_contract_actions():
            contract_actions_dialog.close()
        
        def cancel_pending_docs():
            pending_docs_dialog.close()
        
        # Bind button events
        contract_actions_btn.on_click(open_contract_actions)
        pending_docs_btn.on_click(open_pending_docs)
        process_btn.on_click(process_contract_action)
        upload_btn.on_click(upload_pending_documents)
        cancel_actions_btn.on_click(cancel_contract_actions)
        cancel_upload_btn.on_click(cancel_pending_docs)




