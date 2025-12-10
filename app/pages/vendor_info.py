from nicegui import ui
from datetime import datetime
from app.models.vendor import DocumentType

def vendor_info(vendor_id: int):
    """Display vendor information by ID"""
    # Fetch vendor from database
    from app.db.database import SessionLocal
    from app.services.vendor_service import VendorService
    from sqlalchemy.orm import joinedload
    
    vendor = None
    db = SessionLocal()
    try:
        # Eagerly load all relationships to avoid DetachedInstanceError
        from app.models.vendor import Vendor
        vendor = db.query(Vendor).options(
            joinedload(Vendor.emails),
            joinedload(Vendor.addresses),
            joinedload(Vendor.phones),
            joinedload(Vendor.documents)
        ).filter(Vendor.id == vendor_id).first()
        
        if not vendor:
            print(f"Vendor with ID {vendor_id} not found")
    except Exception as e:
        print(f"Error loading vendor data: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
    
    # Navigation
    with ui.row().classes("max-w-3xl mx-auto mt-4"):
        with ui.link(target='/vendors').classes('no-underline'):
            ui.button("Back to Vendors List", icon="arrow_back").props('flat color=primary')
    
    # Basic info
    with ui.card().classes("w-full max-w-3xl mx-auto mt-4 p-6"):
        ui.label("Vendor Info").classes("text-h5 mb-4")
        
        if not vendor:
            ui.label("No vendor selected. Please select a vendor from the vendors list.").classes("text-red-600")
        else:
            # Get primary email
            primary_email = next((e.email for e in vendor.emails if e.is_primary), 
                                vendor.emails[0].email if vendor.emails else "N/A")
            
            # Get primary address
            primary_address = next((a for a in vendor.addresses if a.is_primary),
                                  vendor.addresses[0] if vendor.addresses else None)
            
            # Get primary phone
            primary_phone = next((p for p in vendor.phones if p.is_primary),
                                vendor.phones[0] if vendor.phones else None)
            
            with ui.row().classes("mb-2 gap-4"):
                ui.label(f"Vendor ID: {vendor.vendor_id}").classes("font-bold")
                ui.label(f"Vendor Name: {vendor.vendor_name}").classes("font-bold")
            with ui.row().classes("mb-2 items-center gap-4"):
                with ui.row().classes("items-center gap-2"):
                    ui.label("Status:").classes("text-lg font-bold")
                    status_color = "green" if vendor.status.value == "Active" else "red"
                    ui.badge(vendor.status.value, color=status_color).classes("text-sm font-semibold")
                ui.label(f"Contact Person: {vendor.vendor_contact_person}")
                ui.label(f"Email: {primary_email}")
            with ui.row().classes("mb-2"):
                next_dd_date = vendor.next_required_due_diligence_date.strftime("%Y-%m-%d") if vendor.next_required_due_diligence_date else "N/A"
                ui.label(f"Next Required Due Diligence Date: {next_dd_date}")

            more = ui.button("More", icon="expand_more").props("flat")
            details_card = ui.card().classes("mt-4 hidden")

            def toggle_details():
                if "hidden" in details_card._classes:
                    details_card.classes(remove="hidden")
                    more.props("icon=expand_less")
                    more.set_text("Less")
                else:
                    details_card.classes(add="hidden")
                    more.props("icon=expand_more")
                    more.set_text("More")
            more.on("click", toggle_details)

            with details_card:
                ui.label("All Vendor Details").classes("text-h6 mb-2")
                with ui.row().classes("gap-4"):
                    if primary_address:
                        ui.label(f"Address: {primary_address.address}")
                        ui.label(f"City: {primary_address.city}")
                        ui.label(f"State: {primary_address.state}")
                        ui.label(f"Zip: {primary_address.zip_code}")
                    else:
                        ui.label("Address: N/A")
                with ui.row().classes("gap-4 mt-2"):
                    ui.label(f"Country: {vendor.vendor_country}")
                with ui.row().classes("gap-4 mt-2"):
                    phone_display = f"{primary_phone.area_code} {primary_phone.phone_number}" if primary_phone else "N/A"
                    ui.label(f"Phone: {phone_display}")
                    ui.label(f"Bank Customer: {vendor.bank_customer.value}")
                    ui.label(f"CIF: {vendor.cif or 'N/A'}")
                with ui.row().classes("gap-4 mt-2"):
                    ui.label(f"Material Outsourcing: {vendor.material_outsourcing_arrangement.value}")
                    last_dd_date = vendor.last_due_diligence_date.strftime("%Y-%m-%d") if vendor.last_due_diligence_date else "N/A"
                    ui.label(f"Last Due Diligence: {last_dd_date}")
                    ui.label(f"Alert Frequency: {vendor.next_required_due_diligence_alert_frequency or 'N/A'}")
                with ui.column().classes("mt-4"):
                    ui.label("Due Diligence Info:").classes("font-bold")
                    ui.label(f"Required: {vendor.due_diligence_required.value}")
                    if vendor.documents:
                        ui.label(f"Documents uploaded: {len(vendor.documents)}")
                        for doc in vendor.documents[:3]:  # Show first 3
                            ui.label(f"  • {doc.document_type.value}: {doc.custom_document_name}").classes("text-sm")
                    else:
                        ui.label("No documents uploaded").classes("text-gray-500")
    
    # Additional Documents Section
    if vendor:
        with ui.card().classes("w-full max-w-3xl mx-auto mt-6 p-6"):
            with ui.row().classes("items-center justify-between w-full mb-4"):
                ui.label("Additional Documents").classes("text-h5 mb-4 text-blue-600")
                additional_docs_btn = ui.button("View Additional Documents", icon="description").props('color=primary size=lg')
            
            # Additional Documents Dialog
            with ui.dialog() as additional_docs_dialog, ui.card().classes("min-w-[800px] max-w-4xl max-h-[80vh] overflow-y-auto"):
                ui.label("Additional Vendor Documents").classes("text-h5 mb-4 text-blue-600 font-bold")
                
                # Organize documents by type
                documents_by_type = {}
                for doc in vendor.documents:
                    doc_type = doc.document_type.value
                    if doc_type not in documents_by_type:
                        documents_by_type[doc_type] = []
                    documents_by_type[doc_type].append(doc)
                
                # Define the document types to display (in order)
                document_types_to_show = [
                    DocumentType.DUE_DILIGENCE.value,
                    DocumentType.NON_DISCLOSURE_AGREEMENT.value,
                    DocumentType.RISK_ASSESSMENT_FORM.value,
                    DocumentType.BUSINESS_CONTINUITY_PLAN.value,
                    DocumentType.DISASTER_RECOVERY_PLAN.value,
                    DocumentType.INSURANCE_POLICY.value,
                ]
                
                # Display each document type section
                for doc_type in document_types_to_show:
                    with ui.card().classes("w-full mb-4 p-4 border-l-4 border-blue-400"):
                        with ui.row().classes("items-center justify-between w-full mb-2"):
                            ui.label(doc_type).classes("text-lg font-bold text-gray-800")
                            
                            # Check if documents exist for this type
                            docs_for_type = documents_by_type.get(doc_type, [])
                            if docs_for_type:
                                # Show indicator that document exists
                                ui.badge(f"{len(docs_for_type)} document(s)", color="green").classes("text-sm")
                            else:
                                # Show "No document available" indicator
                                ui.badge("No document available", color="gray").classes("text-sm")
                        
                        if docs_for_type:
                            # Display each document for this type
                            for doc in docs_for_type:
                                with ui.row().classes("items-center gap-4 p-3 bg-gray-50 rounded-lg mb-2 w-full"):
                                    with ui.column().classes("flex-1"):
                                        ui.label(doc.custom_document_name).classes("font-medium text-gray-800")
                                        # Display issue date (document_signed_date)
                                        issue_date = doc.document_signed_date.strftime("%Y-%m-%d") if doc.document_signed_date else "N/A"
                                        ui.label(f"Issue Date: {issue_date}").classes("text-sm text-gray-600")
                                    
                                    # View/Download buttons
                                    with ui.row().classes("gap-2"):
                                        # View button - opens file in new tab
                                        view_btn = ui.button("View", icon="visibility").props('color=primary flat size=sm')
                                        # Download button
                                        download_btn = ui.button("Download", icon="download").props('color=secondary flat size=sm')
                                        
                                        # View/Download document function - using file path
                                        def make_view_handler(doc_path, doc_name, file_name):
                                            def view_document():
                                                # For PDFs, try to open in browser
                                                # Note: This requires the file to be accessible via a static file server
                                                # For now, we'll trigger download which works universally
                                                ui.notify(f"Opening {doc_name}...", type="info")
                                                # Fallback to download if view not available
                                                make_download_handler(doc_path, doc_name, file_name)()
                                            return view_document
                                        
                                        def make_download_handler(doc_path, doc_name, file_name):
                                            def download_document():
                                                # Read file and create download
                                                import os
                                                if os.path.exists(doc_path):
                                                    # Read file content
                                                    with open(doc_path, 'rb') as f:
                                                        file_content = f.read()
                                                    
                                                    # Convert to base64 for download
                                                    import base64
                                                    b64_content = base64.b64encode(file_content).decode()
                                                    
                                                    # Trigger download
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
                                        
                                        view_btn.on_click(make_view_handler(doc.file_path, doc.custom_document_name, doc.file_name))
                                        download_btn.on_click(make_download_handler(doc.file_path, doc.custom_document_name, doc.file_name))
                        else:
                            # Show "No document available" message
                            with ui.row().classes("p-3 bg-gray-50 rounded-lg w-full"):
                                ui.label("No document available").classes("text-gray-500 italic")
                
                # Close button
                with ui.row().classes("justify-end mt-4 w-full"):
                    ui.button("Close", icon="close", on_click=additional_docs_dialog.close).props('color=primary')
            
            # Function to open additional documents dialog
            def open_additional_docs():
                additional_docs_dialog.open()
            
            additional_docs_btn.on_click(open_additional_docs)


    # Action Buttons Section
    with ui.card().classes("w-full max-w-3xl mx-auto mt-6 p-6"):
        ui.label("Contract Actions").classes("text-h5 mb-4 text-blue-600")
        
        with ui.row().classes("gap-4 w-full justify-center"):
            # Contract Actions Button
            contract_actions_btn = ui.button("Contract Actions", icon="settings").props('color=primary size=lg')
            
            # Pending Documents Button
            pending_docs_btn = ui.button("Pending Documents", icon="upload").props('color=orange size=lg')
        
        # Contract Termination Dialog
        with ui.dialog() as contract_actions_dialog, ui.card().classes("min-w-[600px] max-w-3xl"):
            ui.label("Contract Termination Decision").classes("text-h5 mb-4 text-red-600")
            
            # Contract details
            with ui.row().classes("mb-4 p-4 bg-gray-50 rounded-lg w-full"):
                with ui.column():
                    ui.label("Contract ID: CTR-2024-001").classes("font-bold text-lg")
                    ui.label("Vendor: Acme Corp").classes("text-gray-600")
                    ui.label("Expiration Date: 2024-01-15").classes("text-gray-600")
                    ui.label("Status: Expired (5 days past due)").classes("text-red-600 font-bold")
            
            # Termination decision form
            with ui.column().classes("space-y-4 w-full"):
                ui.label("Termination Decision").classes("text-lg font-bold")
                
                # Decision options
                with ui.row().classes("gap-4"):
                    terminate_radio = ui.radio(['Terminate', 'Renew', 'Extend'], value='Terminate').props('inline')
                
                # Termination reason
                with ui.column().classes("w-full"):
                    ui.label("Termination Reason").classes("font-medium")
                    termination_reason = ui.textarea(placeholder="Enter reason for termination...").classes("w-full").props('outlined')
                
                # Action buttons
                with ui.row().classes("gap-4 mt-6"):
                    save_decision_btn = ui.button("Save Termination Decision", icon="save").props('color=red')
                    cancel_actions_btn = ui.button("Cancel", icon="cancel").props('color=grey')
                    
                    # Action buttons (initially hidden)
                    with ui.row().classes("gap-2 mt-4"):
                        complete_btn = ui.button("COMPLETE", icon="check_circle").props('color=green')
                        send_back_btn = ui.button("SEND BACK", icon="arrow_back").props('color=orange')
                    complete_btn.visible = False
                    send_back_btn.visible = False
            
            # Status indicator
            status_indicator = ui.element("div").classes("mt-4 p-4 rounded-lg hidden")
            
            # Instructions
            with ui.card().classes("mt-6 p-4 bg-blue-50 border-l-4 border-blue-400 w-full"):
                ui.label("Instructions:").classes("font-bold text-blue-800")
                ui.label("• Select 'Terminate' to save your termination decision").classes("text-blue-700")
                ui.label("• You can optionally provide a reason for termination").classes("text-blue-700")
                ui.label("• After saving, the contract will be marked as 'Termination Pending – Documents Required'").classes("text-blue-700")
                ui.label("• Required documents can be uploaded later from the Pending Documents for Termination workbasket").classes("text-blue-700")
        
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
                
                # Show action buttons
                complete_btn.visible = True
                send_back_btn.visible = True
                
                # Hide the form
                terminate_radio.visible = False
                termination_reason.visible = False
                save_decision_btn.visible = False
                cancel_actions_btn.visible = False
                
                ui.notify("Termination decision saved! Contract marked as 'Termination Pending – Documents Required'", type="positive")
            else:
                ui.notify("Please select 'Terminate' to save a termination decision", type="warning")
        
        # Function to handle cancel
        def cancel_termination():
            terminate_radio.value = 'Terminate'
            termination_reason.value = ""
            contract_actions_dialog.close()
        
        # Function to handle complete action
        def handle_complete():
            ui.notify("Contract marked as complete", type="positive")
            contract_actions_dialog.close()
        
        # Function to handle send back action
        def handle_send_back():
            ui.notify("Contract sent back for review", type="info")
            contract_actions_dialog.close()
        
        def upload_pending_documents():
            if not pending_file_upload.value:
                ui.notify("No documents selected", type="warning")
                return
            ui.notify("Documents uploaded successfully", type="positive")
            pending_docs_dialog.close()
        
        def cancel_pending_docs():
            pending_docs_dialog.close()
        
        # Bind button events
        contract_actions_btn.on_click(open_contract_actions)
        pending_docs_btn.on_click(open_pending_docs)
        save_decision_btn.on_click(save_termination_decision)
        cancel_actions_btn.on_click(cancel_termination)
        complete_btn.on_click(handle_complete)
        send_back_btn.on_click(handle_send_back)
        upload_btn.on_click(upload_pending_documents)
        cancel_upload_btn.on_click(cancel_pending_docs)




