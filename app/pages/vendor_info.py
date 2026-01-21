from nicegui import ui
from datetime import datetime, date
from app.models.vendor import DocumentType

def vendor_info(vendor_id: int):
    """Display vendor information by ID"""
    # Fetch vendor from database
    from app.db.database import SessionLocal
    from app.services.vendor_service import VendorService
    from sqlalchemy.orm import joinedload
    
    vendor = None
    contracts = []
    contract_documents_count = 0
    db = SessionLocal()
    try:
        # Eagerly load all relationships to avoid DetachedInstanceError
        from app.models.vendor import Vendor
        from app.models.contract import Contract
        vendor = db.query(Vendor).options(
            joinedload(Vendor.emails),
            joinedload(Vendor.addresses),
            joinedload(Vendor.phones),
            joinedload(Vendor.documents)
        ).filter(Vendor.id == vendor_id).first()
        
        if vendor:
            # Load contracts with their documents
            contracts = db.query(Contract).options(
                joinedload(Contract.documents)
            ).filter(Contract.vendor_id == vendor.id).all()
            
            # Count all contract documents across all contracts
            for contract in contracts:
                contract_documents_count += len(contract.documents)
        
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
        with ui.row().classes("items-center justify-between mb-4 w-full"):
            ui.label("Vendor Info").classes("text-h5")
            if vendor:
                with ui.row().classes("items-center gap-2"):
                    edit_btn = ui.button(icon="edit").props('flat round color=primary size=sm').tooltip('Edit Vendor Info')
        
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
                    # Status coloring: Active = green, Inactive = black (per requirements)
                    status_color = "green" if vendor.status.value == "Active" else "black"
                    ui.badge(vendor.status.value, color=status_color).classes("text-sm font-semibold")
                ui.label(f"Contact Person: {vendor.vendor_contact_person}")
                ui.label(f"Email: {primary_email}")
            with ui.row().classes("mb-2 items-center gap-2"):
                ui.label("Next Required Due Diligence Date:").classes("font-medium")
                if vendor.next_required_due_diligence_date:
                    next_dd_date = vendor.next_required_due_diligence_date.strftime("%Y-%m-%d")
                    # Check if due diligence date has passed
                    if isinstance(vendor.next_required_due_diligence_date, datetime):
                        dd_date = vendor.next_required_due_diligence_date.date()
                    else:
                        dd_date = vendor.next_required_due_diligence_date
                    
                    if dd_date < date.today():
                        # Date has passed - display in red with attention icon
                        with ui.row().classes("items-center gap-2"):
                            ui.icon("warning", color="red").classes("text-xl")
                            ui.label(next_dd_date).classes("text-red-600 font-bold")
                    else:
                        ui.label(next_dd_date)
                else:
                    ui.label("N/A")

            more = ui.button("More", icon="expand_more").props("flat")
            details_card = ui.card().classes("mt-4 hidden w-full")

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
                with ui.row().classes("gap-4 w-full"):
                    if primary_address:
                        ui.label(f"Address: {primary_address.address}")
                        ui.label(f"City: {primary_address.city}")
                        ui.label(f"State: {primary_address.state}")
                        ui.label(f"Zip: {primary_address.zip_code}")
                    else:
                        ui.label("Address: N/A")
                with ui.row().classes("gap-4 mt-2 w-full"):
                    ui.label(f"Country: {vendor.vendor_country}")
                with ui.row().classes("gap-4 mt-2 w-full"):
                    phone_display = f"{primary_phone.area_code} {primary_phone.phone_number}" if primary_phone else "N/A"
                    ui.label(f"Phone: {phone_display}")
                    ui.label(f"Bank Customer: {vendor.bank_customer.value}")
                    ui.label(f"CIF: {vendor.cif or 'N/A'}")
                with ui.row().classes("gap-4 mt-2 w-full"):
                    ui.label(f"Material Outsourcing: {vendor.material_outsourcing_arrangement.value}")
                    if vendor.last_due_diligence_date:
                        last_dd_date = vendor.last_due_diligence_date.strftime("%Y-%m-%d")
                        # Check if last due diligence date has passed
                        if isinstance(vendor.last_due_diligence_date, datetime):
                            last_dd_date_obj = vendor.last_due_diligence_date.date()
                        else:
                            last_dd_date_obj = vendor.last_due_diligence_date
                        
                        if last_dd_date_obj < date.today():
                            # Date has passed - display in red with attention icon
                            with ui.row().classes("items-center gap-2"):
                                ui.icon("warning", color="red").classes("text-xl")
                                ui.label(f"Last Due Diligence: {last_dd_date}").classes("text-red-600 font-bold")
                        else:
                            ui.label(f"Last Due Diligence: {last_dd_date}")
                    else:
                        ui.label("Last Due Diligence: N/A")
                    # Display alert frequency value (e.g., "30 days" instead of enum)
                    alert_freq = vendor.next_required_due_diligence_alert_frequency.value if vendor.next_required_due_diligence_alert_frequency else 'N/A'
                    ui.label(f"Alert Frequency: {alert_freq}")
                with ui.column().classes("mt-4"):
                    ui.label("Due Diligence Info:").classes("font-bold")
                    ui.label(f"Required: {vendor.due_diligence_required.value}")
                    if vendor.documents:
                        ui.label(f"Documents uploaded: {len(vendor.documents)}")
                        for doc in vendor.documents[:3]:  # Show first 3
                            ui.label(f"  • {doc.document_type.value}: {doc.custom_document_name}").classes("text-sm")
                    else:
                        ui.label("No documents uploaded").classes("text-gray-500")
    
    # Edit Vendor Dialog
    if vendor:
        from app.models.vendor import MaterialOutsourcingType, BankCustomerType, DueDiligenceRequiredType, AlertFrequencyType, VendorStatusType
        
        with ui.dialog() as edit_dialog, ui.card().classes("min-w-[900px] max-w-5xl max-h-[90vh] overflow-y-auto"):
            ui.label("Edit Vendor Information").classes("text-h5 mb-4 text-blue-600 font-bold")
            
            # Store original values for change tracking
            original_values = {}
            edited_fields = {}
            
            # Track if any changes were made
            has_changes_ref = {'value': False}
            
            with ui.column().classes("w-full gap-4"):
                # Vendor ID (Read-only)
                with ui.row().classes("gap-4 items-center"):
                    ui.label(f"Vendor ID: {vendor.vendor_id}").classes("font-bold text-lg")
                
                # Vendor Name
                with ui.column().classes("w-full"):
                    ui.label("Vendor Name *").classes("font-medium text-sm")
                    vendor_name_input = ui.input(
                        value=vendor.vendor_name,
                        placeholder="Enter vendor name"
                    ).classes("w-full").props('outlined dense')
                    original_values['vendor_name'] = vendor.vendor_name
                
                # Contact Person
                with ui.column().classes("w-full"):
                    ui.label("Contact Person *").classes("font-medium text-sm")
                    contact_person_input = ui.input(
                        value=vendor.vendor_contact_person,
                        placeholder="Enter contact person"
                    ).classes("w-full").props('outlined dense')
                    original_values['vendor_contact_person'] = vendor.vendor_contact_person
                
                # Country
                with ui.column().classes("w-full"):
                    ui.label("Country *").classes("font-medium text-sm")
                    country_input = ui.input(
                        value=vendor.vendor_country,
                        placeholder="Enter country"
                    ).classes("w-full").props('outlined dense')
                    original_values['vendor_country'] = vendor.vendor_country
                
                # Status
                with ui.column().classes("w-full"):
                    ui.label("Status *").classes("font-medium text-sm")
                    status_select = ui.select(
                        options=[status.value for status in VendorStatusType],
                        value=vendor.status.value
                    ).classes("w-full").props('outlined dense')
                    original_values['status'] = vendor.status.value
                
                # Bank Customer
                with ui.column().classes("w-full"):
                    ui.label("Bank Customer *").classes("font-medium text-sm")
                    bank_customer_select = ui.select(
                        options=[bc.value for bc in BankCustomerType],
                        value=vendor.bank_customer.value
                    ).classes("w-full").props('outlined dense')
                    original_values['bank_customer'] = vendor.bank_customer.value
                
                # CIF (conditionally required)
                with ui.column().classes("w-full"):
                    ui.label("CIF (6 digits, required for Aruba/Orco Bank)").classes("font-medium text-sm")
                    cif_input = ui.input(
                        value=vendor.cif or "",
                        placeholder="Enter CIF"
                    ).classes("w-full").props('outlined dense maxlength=6')
                    original_values['cif'] = vendor.cif or ""
                
                # Material Outsourcing
                with ui.column().classes("w-full"):
                    ui.label("Material Outsourcing Arrangement *").classes("font-medium text-sm")
                    material_outsourcing_select = ui.select(
                        options=[mo.value for mo in MaterialOutsourcingType],
                        value=vendor.material_outsourcing_arrangement.value
                    ).classes("w-full").props('outlined dense')
                    original_values['material_outsourcing_arrangement'] = vendor.material_outsourcing_arrangement.value
                
                # Due Diligence Required
                with ui.column().classes("w-full"):
                    ui.label("Due Diligence Required *").classes("font-medium text-sm")
                    due_diligence_select = ui.select(
                        options=[dd.value for dd in DueDiligenceRequiredType],
                        value=vendor.due_diligence_required.value
                    ).classes("w-full").props('outlined dense')
                    original_values['due_diligence_required'] = vendor.due_diligence_required.value
                
                # Last Due Diligence Date
                with ui.column().classes("w-full"):
                    ui.label("Last Due Diligence Date").classes("font-medium text-sm")
                    last_dd_date_value = vendor.last_due_diligence_date.strftime("%Y-%m-%d") if vendor.last_due_diligence_date else ""
                    last_dd_date_input = ui.input(
                        value=last_dd_date_value,
                        placeholder="YYYY-MM-DD"
                    ).classes("w-full").props('outlined dense type=date')
                    original_values['last_due_diligence_date'] = last_dd_date_value
                
                # Next Required Due Diligence Date
                with ui.column().classes("w-full"):
                    ui.label("Next Required Due Diligence Date").classes("font-medium text-sm")
                    next_dd_date_value = vendor.next_required_due_diligence_date.strftime("%Y-%m-%d") if vendor.next_required_due_diligence_date else ""
                    next_dd_date_input = ui.input(
                        value=next_dd_date_value,
                        placeholder="YYYY-MM-DD"
                    ).classes("w-full").props('outlined dense type=date')
                    original_values['next_required_due_diligence_date'] = next_dd_date_value
                
                # Alert Frequency
                with ui.column().classes("w-full"):
                    ui.label("Next Required Due Diligence Alert Frequency").classes("font-medium text-sm")
                    alert_freq_options = [af.value for af in AlertFrequencyType]
                    alert_freq_value = vendor.next_required_due_diligence_alert_frequency.value if vendor.next_required_due_diligence_alert_frequency else alert_freq_options[0]
                    alert_freq_select = ui.select(
                        options=alert_freq_options,
                        value=alert_freq_value
                    ).classes("w-full").props('outlined dense')
                    original_values['next_required_due_diligence_alert_frequency'] = alert_freq_value
                
                # Track changes
                def track_change(field_name):
                    def on_change(e):
                        current_value = e.value if hasattr(e, 'value') else e
                        if str(current_value) != str(original_values.get(field_name, '')):
                            edited_fields[field_name] = current_value
                            has_changes_ref['value'] = True
                        elif field_name in edited_fields:
                            del edited_fields[field_name]
                            has_changes_ref['value'] = len(edited_fields) > 0
                    return on_change
                
                vendor_name_input.on('change', track_change('vendor_name'))
                contact_person_input.on('change', track_change('vendor_contact_person'))
                country_input.on('change', track_change('vendor_country'))
                status_select.on('change', track_change('status'))
                bank_customer_select.on('change', track_change('bank_customer'))
                cif_input.on('change', track_change('cif'))
                material_outsourcing_select.on('change', track_change('material_outsourcing_arrangement'))
                due_diligence_select.on('change', track_change('due_diligence_required'))
                last_dd_date_input.on('change', track_change('last_due_diligence_date'))
                next_dd_date_input.on('change', track_change('next_required_due_diligence_date'))
                alert_freq_select.on('change', track_change('next_required_due_diligence_alert_frequency'))
                
                # Buttons
                with ui.row().classes("gap-4 mt-6 w-full justify-end"):
                    ui.button("Cancel", icon="cancel", on_click=lambda: edit_dialog.close()).props('flat color=grey')
                    save_btn = ui.button("Save Changes", icon="save", on_click=lambda: save_vendor_changes()).props('color=primary')
        
        # Save changes function
        async def save_vendor_changes():
            if not has_changes_ref['value']:
                ui.notify("No changes to save", type="info")
                return
            
            try:
                # Build update payload
                update_data = {}
                
                if 'vendor_name' in edited_fields:
                    update_data['vendor_name'] = vendor_name_input.value
                if 'vendor_contact_person' in edited_fields:
                    update_data['vendor_contact_person'] = contact_person_input.value
                if 'vendor_country' in edited_fields:
                    update_data['vendor_country'] = country_input.value
                if 'status' in edited_fields:
                    update_data['status'] = status_select.value
                if 'bank_customer' in edited_fields:
                    update_data['bank_customer'] = bank_customer_select.value
                if 'cif' in edited_fields:
                    update_data['cif'] = cif_input.value if cif_input.value else None
                if 'material_outsourcing_arrangement' in edited_fields:
                    update_data['material_outsourcing_arrangement'] = material_outsourcing_select.value
                if 'due_diligence_required' in edited_fields:
                    update_data['due_diligence_required'] = due_diligence_select.value
                if 'last_due_diligence_date' in edited_fields:
                    update_data['last_due_diligence_date'] = last_dd_date_input.value if last_dd_date_input.value else None
                if 'next_required_due_diligence_date' in edited_fields:
                    update_data['next_required_due_diligence_date'] = next_dd_date_input.value if next_dd_date_input.value else None
                if 'next_required_due_diligence_alert_frequency' in edited_fields:
                    update_data['next_required_due_diligence_alert_frequency'] = alert_freq_select.value
                
                # Make API call
                import httpx
                from app.core.config import settings
                
                api_url = f"http://localhost:8000{settings.api_v1_prefix}/vendors/{vendor.id}"
                
                async with httpx.AsyncClient() as client:
                    response = await client.put(
                        api_url,
                        json=update_data,
                        timeout=30.0
                    )
                    
                    if response.status_code == 200:
                        ui.notify("✅ Vendor information updated successfully!", type="positive")
                        edit_dialog.close()
                        # Refresh the page to show updated data
                        ui.navigate.to(f'/vendor-info/{vendor.id}')
                    else:
                        error_detail = response.json().get('detail', 'Unknown error')
                        ui.notify(f"❌ Error updating vendor: {error_detail}", type="negative")
            except Exception as e:
                ui.notify(f"❌ Error: {str(e)}", type="negative")
                print(f"Error updating vendor: {e}")
                import traceback
                traceback.print_exc()
        
        # Bind edit button to open dialog
        def open_edit_dialog():
            # Reset changes tracking
            edited_fields.clear()
            has_changes_ref['value'] = False
            # Reset input values to current vendor data
            vendor_name_input.value = vendor.vendor_name
            contact_person_input.value = vendor.vendor_contact_person
            country_input.value = vendor.vendor_country
            status_select.value = vendor.status.value
            bank_customer_select.value = vendor.bank_customer.value
            cif_input.value = vendor.cif or ""
            material_outsourcing_select.value = vendor.material_outsourcing_arrangement.value
            due_diligence_select.value = vendor.due_diligence_required.value
            last_dd_date_input.value = vendor.last_due_diligence_date.strftime("%Y-%m-%d") if vendor.last_due_diligence_date else ""
            next_dd_date_input.value = vendor.next_required_due_diligence_date.strftime("%Y-%m-%d") if vendor.next_required_due_diligence_date else ""
            alert_freq_select.value = vendor.next_required_due_diligence_alert_frequency.value if vendor.next_required_due_diligence_alert_frequency else alert_freq_options[0]
            edit_dialog.open()
        
        edit_btn.on_click(open_edit_dialog)
    
    # Documents Section - Two Categories
    if vendor:
        with ui.card().classes("w-full max-w-3xl mx-auto mt-6 p-6"):
            ui.label("Documents").classes("text-h5 mb-4 text-blue-600 font-bold")
            
            # Calculate document counts
            supporting_docs_count = len(vendor.documents) if vendor.documents else 0
            
            with ui.row().classes("gap-6 w-full"):
                # Vendor Contracts Category
                contracts_card = ui.card().classes("flex-1 p-6 border-2 border-blue-300 hover:border-blue-500 cursor-pointer transition-all")
                with contracts_card:
                    with ui.column().classes("items-center text-center gap-3"):
                        ui.icon("description", size="48px", color="blue").classes("mb-2")
                        ui.label("Vendor Contracts").classes("text-lg font-bold text-blue-700")
                        
                        if contract_documents_count > 0:
                            ui.badge(f"{contract_documents_count} document(s)", color="green").classes("text-sm font-semibold")
                        else:
                            ui.label("No documents available").classes("text-gray-500 italic text-sm")
                
                # Click handler for contracts - navigate to contracts overview page
                def navigate_to_contracts():
                    ui.navigate.to(f'/vendor-contracts/{vendor.id}')
                
                contracts_card.on("click", navigate_to_contracts)
                
                # Supporting Documents Category
                supporting_card = ui.card().classes("flex-1 p-6 border-2 border-green-300 hover:border-green-500 cursor-pointer transition-all")
                supporting_badge_container = None
                
                def update_supporting_docs_badge():
                    """Update the supporting documents badge count"""
                    nonlocal supporting_badge_container
                    current_count = len(vendor.documents) if vendor and vendor.documents else 0
                    if supporting_badge_container:
                        supporting_badge_container.clear()
                        with supporting_badge_container:
                            if current_count > 0:
                                ui.badge(f"{current_count} document(s)", color="green").classes("text-sm font-semibold")
                            else:
                                ui.label("No documents available").classes("text-gray-500 italic text-sm")
                
                with supporting_card:
                    with ui.column().classes("items-center text-center gap-3"):
                        ui.icon("folder", size="48px", color="green").classes("mb-2")
                        ui.label("Supporting Documents").classes("text-lg font-bold text-green-700")
                        
                        supporting_badge_container = ui.column().classes("items-center")
                        update_supporting_docs_badge()
                
                # Click handler for supporting documents
                def open_supporting_documents():
                    # Refresh vendor data before opening
                    refresh_supporting_docs()
                    update_supporting_docs_badge()
                    supporting_docs_dialog.open()
                
                supporting_card.on("click", open_supporting_documents)
            
            # Supporting Documents Dialog
            with ui.dialog() as supporting_docs_dialog, ui.card().classes("min-w-[800px] max-w-4xl max-h-[80vh] overflow-y-auto") as dialog_card:
                dialog_content_container = ui.column().classes("w-full")
                
                def refresh_supporting_docs():
                    """Refresh supporting documents by reloading vendor data"""
                    nonlocal vendor, supporting_docs_count
                    
                    from app.db.database import SessionLocal
                    from sqlalchemy.orm import joinedload
                    from app.models.vendor import Vendor
                    db = SessionLocal()
                    try:
                        vendor = db.query(Vendor).options(
                            joinedload(Vendor.documents)
                        ).filter(Vendor.id == vendor_id).first()
                        supporting_docs_count = len(vendor.documents) if vendor.documents else 0
                    finally:
                        db.close()
                    
                    # Update the badge on the main card
                    update_supporting_docs_badge()
                    
                    # Rebuild dialog content
                    dialog_content_container.clear()
                    build_supporting_docs_content()
                
                def build_supporting_docs_content():
                    """Build the content of the supporting documents dialog"""
                    with dialog_content_container:
                        ui.label("Supporting Documents").classes("text-h5 mb-4 text-green-600 font-bold")
                        
                        # Refresh count from current vendor data
                        current_count = len(vendor.documents) if vendor.documents else 0
                        
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
                            DocumentType.INTEGRITY_POLICY.value,
                        ]
                        
                        # Display each document type section
                        for doc_type in document_types_to_show:
                            with ui.card().classes("w-full mb-4 p-4 border-l-4 border-green-400"):
                                with ui.row().classes("items-center justify-between w-full mb-2"):
                                    ui.label(doc_type).classes("text-lg font-bold text-gray-800")
                                    
                                    docs_for_type = documents_by_type.get(doc_type, [])
                                    count_badge = ui.badge(
                                        f"{len(docs_for_type)} document(s)" if docs_for_type else "No document available",
                                        color="green" if docs_for_type else "gray"
                                    ).classes("text-sm")
                                    
                                    # Add (+) button for each document type
                                    add_btn = ui.button(icon="add", color="green").props('flat round size=sm').tooltip('Add Document')
                                    
                                    def open_add_document_dialog(document_type_val=doc_type):
                                        """Open dialog to add a new document of this type"""
                                        with ui.dialog() as add_doc_dialog, ui.card().classes("min-w-[500px]"):
                                            ui.label(f"Add {document_type_val} Document").classes("text-h6 mb-4")
                                            
                                            doc_name_input = ui.input("Document Name", placeholder="Enter document name").classes("w-full mb-3").props('outlined')
                                            issue_date_input = ui.input("Issue Date *", placeholder="YYYY-MM-DD").classes("w-full mb-3").props('outlined type=date required')
                                            
                                            file_upload = ui.upload(
                                                on_upload=lambda e: ui.notify(f'File selected: {e.name}'),
                                                max_file_size=10_000_000,
                                                max_files=1
                                            ).classes('w-full mb-4').props('accept=.pdf')
                                            
                                            def save_new_document():
                                                if not issue_date_input.value:
                                                    ui.notify("Issue Date is required", type="negative")
                                                    return
                                                
                                                if not file_upload.value:
                                                    ui.notify("Please select a file to upload", type="negative")
                                                    return
                                                
                                                # Upload document via API
                                                import httpx
                                                import asyncio
                                                
                                                async def upload_document():
                                                    try:
                                                        files = {'file': (file_upload.value[0].name, file_upload.value[0].content, 'application/pdf')}
                                                        data = {
                                                            'document_type': document_type_val,
                                                            'custom_document_name': doc_name_input.value or file_upload.value[0].name,
                                                            'document_signed_date': issue_date_input.value
                                                        }
                                                        
                                                        async with httpx.AsyncClient(timeout=30.0) as client:
                                                            response = await client.post(
                                                                f"http://localhost:8000/api/v1/vendors/{vendor_id}/documents",
                                                                files=files,
                                                                data=data
                                                            )
                                                            
                                                            if response.status_code == 200:
                                                                ui.notify(f"Document added successfully!", type="positive")
                                                                add_doc_dialog.close()
                                                                refresh_supporting_docs()
                                                            else:
                                                                error_detail = response.json().get('detail', 'Unknown error')
                                                                ui.notify(f"Error adding document: {error_detail}", type="negative")
                                                    except Exception as e:
                                                        ui.notify(f"Error: {str(e)}", type="negative")
                                                        print(f"Error uploading document: {e}")
                                                
                                                asyncio.create_task(upload_document())
                                            
                                            with ui.row().classes("gap-2 justify-end w-full mt-4"):
                                                ui.button("Cancel", on_click=add_doc_dialog.close).props('flat')
                                                ui.button("Save", icon="save", on_click=save_new_document).props('color=primary')
                                        
                                        add_doc_dialog.open()
                                    
                                    add_btn.on_click(lambda dt=doc_type: open_add_document_dialog(dt))
                                
                                docs_for_type = documents_by_type.get(doc_type, [])
                                if docs_for_type:
                                    for doc in docs_for_type:
                                        with ui.row().classes("items-center gap-4 p-3 bg-gray-50 rounded-lg mb-2 w-full"):
                                            with ui.column().classes("flex-1"):
                                                ui.label(doc.custom_document_name).classes("font-medium text-gray-800")
                                                issue_date = doc.document_signed_date.strftime("%Y-%m-%d") if doc.document_signed_date else "N/A"
                                                ui.label(f"Issue Date: {issue_date}").classes("text-sm text-gray-600")
                                            
                                            # Action buttons: View, Download, Edit, Delete
                                            with ui.row().classes("gap-2"):
                                                view_btn = ui.button(icon="visibility").props('color=primary flat round size=sm').tooltip('View')
                                                download_btn = ui.button(icon="download").props('color=secondary flat round size=sm').tooltip('Download')
                                                edit_btn = ui.button(icon="edit").props('color=orange flat round size=sm').tooltip('Edit')
                                                delete_btn = ui.button(icon="delete").props('color=negative flat round size=sm').tooltip('Delete')
                                                
                                                def make_view_handler(doc_path, doc_name, file_name):
                                                    def view_document():
                                                        ui.notify(f"Opening {doc_name}...", type="info")
                                                        make_download_handler(doc_path, doc_name, file_name)()
                                                    return view_document
                                                
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
                                                
                                                def open_edit_dialog(doc_obj):
                                                    """Open dialog to edit document metadata"""
                                                    with ui.dialog() as edit_doc_dialog, ui.card().classes("min-w-[500px]"):
                                                        ui.label(f"Edit {doc_obj.custom_document_name}").classes("text-h6 mb-4")
                                                        
                                                        doc_name_edit = ui.input("Document Name", value=doc_obj.custom_document_name).classes("w-full mb-3").props('outlined')
                                                        issue_date_edit = ui.input(
                                                            "Issue Date *",
                                                            value=doc_obj.document_signed_date.strftime("%Y-%m-%d") if doc_obj.document_signed_date else ""
                                                        ).classes("w-full mb-3").props('outlined type=date required')
                                                        
                                                        def save_edited_document():
                                                            if not issue_date_edit.value:
                                                                ui.notify("Issue Date is required", type="negative")
                                                                return
                                                            
                                                            import httpx
                                                            import asyncio
                                                            
                                                            async def update_document():
                                                                try:
                                                                    data = {
                                                                        'custom_document_name': doc_name_edit.value,
                                                                        'document_signed_date': issue_date_edit.value
                                                                    }
                                                                    
                                                                    async with httpx.AsyncClient(timeout=30.0) as client:
                                                                        response = await client.patch(
                                                                            f"http://localhost:8000/api/v1/vendors/{vendor_id}/documents/{doc_obj.id}",
                                                                            data=data
                                                                        )
                                                                        
                                                                        if response.status_code == 200:
                                                                            ui.notify(f"Document updated successfully!", type="positive")
                                                                            edit_doc_dialog.close()
                                                                            refresh_supporting_docs()
                                                                        else:
                                                                            error_detail = response.json().get('detail', 'Unknown error')
                                                                            ui.notify(f"Error updating document: {error_detail}", type="negative")
                                                                except Exception as e:
                                                                    ui.notify(f"Error: {str(e)}", type="negative")
                                                                    print(f"Error updating document: {e}")
                                                            
                                                            asyncio.create_task(update_document())
                                                        
                                                        with ui.row().classes("gap-2 justify-end w-full mt-4"):
                                                            ui.button("Cancel", on_click=edit_doc_dialog.close).props('flat')
                                                            ui.button("Save", icon="save", on_click=save_edited_document).props('color=primary')
                                                        
                                                        edit_doc_dialog.open()
                                                
                                                def confirm_delete(doc_obj):
                                                    """Confirm and delete document"""
                                                    with ui.dialog() as confirm_dialog, ui.card().classes("min-w-[400px]"):
                                                        ui.label(f"Delete Document").classes("text-h6 mb-2 text-red-600")
                                                        ui.label(f"Are you sure you want to delete '{doc_obj.custom_document_name}'?").classes("mb-4")
                                                        ui.label("This action cannot be undone.").classes("text-sm text-gray-600 mb-4")
                                                        
                                                        def delete_document():
                                                            import httpx
                                                            import asyncio
                                                            
                                                            async def perform_delete():
                                                                try:
                                                                    async with httpx.AsyncClient(timeout=30.0) as client:
                                                                        response = await client.delete(
                                                                            f"http://localhost:8000/api/v1/vendors/{vendor_id}/documents/{doc_obj.id}"
                                                                        )
                                                                        
                                                                        if response.status_code == 204:
                                                                            ui.notify(f"Document deleted successfully!", type="positive")
                                                                            confirm_dialog.close()
                                                                            refresh_supporting_docs()
                                                                        else:
                                                                            error_detail = response.json().get('detail', 'Unknown error') if response.status_code != 204 else None
                                                                            ui.notify(f"Error deleting document: {error_detail or 'Unknown error'}", type="negative")
                                                                except Exception as e:
                                                                    ui.notify(f"Error: {str(e)}", type="negative")
                                                                    print(f"Error deleting document: {e}")
                                                            
                                                            asyncio.create_task(perform_delete())
                                                        
                                                        with ui.row().classes("gap-2 justify-end w-full mt-4"):
                                                            ui.button("Cancel", on_click=confirm_dialog.close).props('flat')
                                                            ui.button("Delete", icon="delete", on_click=delete_document).props('color=negative')
                                                        
                                                        confirm_dialog.open()
                                                
                                                view_btn.on_click(make_view_handler(doc.file_path, doc.custom_document_name, doc.file_name))
                                                download_btn.on_click(make_download_handler(doc.file_path, doc.custom_document_name, doc.file_name))
                                                edit_btn.on_click(lambda d=doc: open_edit_dialog(d))
                                                delete_btn.on_click(lambda d=doc: confirm_delete(d))
                                else:
                                    with ui.row().classes("p-3 bg-gray-50 rounded-lg w-full"):
                                        ui.label("No document available").classes("text-gray-500 italic")
                        
                        if current_count == 0:
                            with ui.row().classes("p-6 w-full justify-center"):
                                ui.label("No supporting documents available").classes("text-gray-500 italic text-lg")
                        
                        # Close button
                        with ui.row().classes("justify-end mt-4 w-full"):
                            ui.button("Close", icon="close", on_click=supporting_docs_dialog.close).props('color=primary')
                
                # Build initial content
                build_supporting_docs_content()




