from nicegui import ui
import httpx
import json
import os
from app.core.config import settings


def new_contract():
    # Fetch vendors from database for vendor selection
    from app.db.database import SessionLocal
    from app.services.vendor_service import VendorService
    from app.services.contract_service import ContractService
    
    db = SessionLocal()
    try:
        vendor_service = VendorService(db)
        # Only load Active vendors for contract creation (exclude Terminated and Inactive vendors)
        vendors_list, _ = vendor_service.get_vendors_with_filters(
            skip=0, limit=1000, status_filter="Active", search=None
        )
        vendor_options = {vendor.vendor_name: vendor.id for vendor in vendors_list}
        vendor_names = (
            list(vendor_options.keys()) if vendor_options else ["No vendors available"]
        )

        contract_service = ContractService(db)
        users_list = contract_service.get_users(active_only=True)
        users_map = {
            f"{user.first_name} {user.last_name}": user.id for user in users_list
        }
    except Exception as e:
        print(f"Error loading initial data: {e}")
        vendor_names = ["Error loading vendors"]
        vendor_options = {}
        users_list = []
        users_map = {}
    finally:
        db.close()

    # Contract Manager / Owner / Backup data with email addresses
    contract_managers_data = {"Please select": ""}
    for user in users_list:
        full_name = f"{user.first_name} {user.last_name}"
        # Avoid overwriting if duplicate names exist
        if full_name not in contract_managers_data:
            contract_managers_data[full_name] = getattr(user, "email", "") or ""
    
    # Vendor Contract variables (function scope for accessibility)
    vendor_contract_uploaded = False
    vendor_contract_file_name = None
    vendor_contract_file_content = None
    vendor_contract_rename_input = None
    vendor_contract_date_input = None
    
    with ui.element("div").classes(
        "flex flex-col items-center justify-center mt-8 w-full"
    ).props(f'id="c213"'):
        # Use real vendors from database
        vendor_select = ui.select(
            options=vendor_names, 
            value=vendor_names[0] if vendor_names else None, 
            label="Select vendor*"
        ).classes("w-64 mt-8 font-[segoe ui]").props("outlined")
        vendor_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
        def validate_vendor(e=None):
            value = vendor_select.value or ''
            if not value.strip():
                vendor_error.text = "Please select a vendor."
                vendor_error.style('display:block')
                vendor_select.classes('border border-red-600')
                return False
            else:
                vendor_error.text = ''
                vendor_error.style('display:none')
                vendor_select.classes(remove='border border-red-600')
                return True
        vendor_select.on('blur', validate_vendor)

        desc_input = ui.input(label="Contract description or purpose*").classes(
            "w-1/2 mt-4 font-[segoe ui]"
        ).props("outlined maxlength=100")
        desc_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
        def validate_desc(e=None):
            value = desc_input.value or ''
            if not value.strip():
                desc_error.text = "Please enter a contract description."
                desc_error.style('display:block')
                desc_input.classes('border border-red-600')
                return False
            else:
                desc_error.text = ''
                desc_error.style('display:none')
                desc_input.classes(remove='border border-red-600')
                return True
        desc_input.on('blur', validate_desc)
        
        # Add contract details section as a div-based table with 4 columns
        with ui.element("div").classes("w-full border rounded border-gray-300 max-w-7xl mt-8 p-6 mx-auto").props(f'id="c203"'):
            # Define style classes as constants to avoid duplication
            label_classes = "text-white font-[segoe ui] py-2 px-4 h-full flex items-center"
            input_classes = "w-full font-[segoe ui]"
            row_classes = "flex w-full"
            std_row_height = "h-auto"

            # Cell classes for consistent styling
            label_cell_classes = "bg-[#144c8e] w-[16.6%] flex items-center"
            input_cell_classes = "bg-white p-2 w-[33.3%]"
            
            # Create a custom table-like layout using divs
            with ui.element("div").classes("w-full border-collapse flex flex-col").props(f'id="c204"'):
                
                # Row 1 - Termination Notice & Contract Expiration Date
                with ui.element('div').classes(f"{row_classes} {std_row_height}"):
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Termination Notice").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes + " flex flex-col"):
                        termination_options = ["15", "30", "60", "90", "120"]
                        termination_input = ui.select(options=termination_options, value="30", label="Days*").classes(input_classes).props("outlined")
                        termination_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
                        def validate_termination(e=None):
                            value = termination_input.value or ''
                            if not value.strip() or value not in termination_options:
                                termination_error.text = "Please select the termination notice in days."
                                termination_error.style('display:block')
                                termination_input.classes('border border-red-600')
                                return False
                            else:
                                termination_error.text = ''
                                termination_error.style('display:none')
                                termination_input.classes(remove='border border-red-600')
                                return True
                        termination_input.on('blur', validate_termination)
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Contract End Date").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        with ui.input('MM/DD/YYYY', value='08/24/2025').classes(input_classes).props("outlined") as end_date:
                            with ui.menu().props('no-parent-event') as end_menu:
                                with ui.date(value='2025-08-24').props('mask=MM/DD/YYYY').bind_value(end_date,
                                    forward=lambda d: d.replace('-', '/') if d else '', 
                                    backward=lambda d: d.replace('/', '-') if d else ''):
                                    with ui.row().classes('justify-end'):
                                        ui.button('Close', on_click=end_menu.close).props('flat')
                            with end_date.add_slot('append'):
                                ui.icon('edit_calendar').on('click', end_menu.open).classes('cursor-pointer')
                
                # Row 2 - Automatic Renewal & Expiration Reminder Notice
                with ui.element('div').classes(f"{row_classes} items-stretch"):
                    with ui.element('div').classes(label_cell_classes + " items-start"):
                        ui.label("Automatic Renewal").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes + " flex flex-col py-2"):
                        auto_renewal_options = ["Please select", "Yes", "No"]
                        auto_renewal_select = ui.select(
                            options=auto_renewal_options, 
                            value="Please select",
                            label="Automatic Renewal*"
                        ).classes(input_classes).props("outlined use-input")
                        auto_renewal_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
                        
                        # Renewal Period field (conditionally shown)
                        renewal_period_options = ["Please select", "1 Year", "2 Years", "3 Years"]
                        renewal_period_select = ui.select(
                            options=renewal_period_options, 
                            value="Please select",
                            label="Renewal Period (Optional)"
                        ).classes(input_classes + " mt-2").props("outlined use-input")
                        renewal_period_select.set_visibility(False)
                        
                        def validate_auto_renewal(e=None):
                            value = auto_renewal_select.value or ''
                            if not value.strip() or value == "Please select":
                                auto_renewal_error.text = "Please indicate if there is an automatic renewal period in place"
                                auto_renewal_error.style('display:block')
                                auto_renewal_select.classes('border border-red-600')
                                renewal_period_select.set_visibility(False)
                                return False
                            else:
                                auto_renewal_error.text = ''
                                auto_renewal_error.style('display:none')
                                auto_renewal_select.classes(remove='border border-red-600')
                                # Show renewal period field only if "Yes" is selected
                                if value == "Yes":
                                    renewal_period_select.set_visibility(True)
                                else:
                                    renewal_period_select.set_visibility(False)
                                    renewal_period_select.value = "Please select"
                                return True
                        
                        auto_renewal_select.on('blur', validate_auto_renewal)
                        auto_renewal_select.on('change', validate_auto_renewal)
                        
                    with ui.element('div').classes(label_cell_classes + " items-start"):
                        ui.label("Expiration Reminder Notice").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes + " flex flex-col py-2"):
                        expiration_options = ["15", "30", "60", "90", "120"]
                        expiration_input = ui.select(options=expiration_options, value="30", label="Days*").classes(input_classes).props("outlined")
                        expiration_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
                        def validate_expiration(e=None):
                            value = expiration_input.value or ''
                            if not value.strip() or value not in expiration_options:
                                expiration_error.text = "Please select the expiration reminder notice in days."
                                expiration_error.style('display:block')
                                expiration_input.classes('border border-red-600')
                                return False
                            else:
                                expiration_error.text = ''
                                expiration_error.style('display:none')
                                expiration_input.classes(remove='border border-red-600')
                                return True
                        expiration_input.on('blur', validate_expiration)
                
                # Row 3 - Type of Contract & Currency
                with ui.element('div').classes(f"{row_classes} {std_row_height}"):
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Type of Contract").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes + " flex flex-col"):
                        contract_type_select = ui.select(options=["Service Agreement", "Maintenance Contract", "Software License", "Consulting Agreement", "Support Contract", "Lease Agreement", "Purchase Agreement", "Non-Disclosure Agreement", "Partnership Agreement", "Outsourcing Agreement"], label="Please Select*").classes(input_classes).props("outlined")
                        contract_type_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
                        def validate_contract_type(e=None):
                            value = contract_type_select.value or ''
                            if not value.strip() or value == "Please Select":
                                contract_type_error.text = "Please select the contract type."
                                contract_type_error.style('display:block')
                                contract_type_select.classes('border border-red-600')
                                return False
                            else:
                                contract_type_error.text = ''
                                contract_type_error.style('display:none')
                                contract_type_select.classes(remove='border border-red-600')
                                return True
                        contract_type_select.on('blur', validate_contract_type)
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Currency").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes + " flex flex-col"):
                        currency_select = ui.select(options=["AWG", "XCG", "USD", "EUR"], label="Please Select*").classes(input_classes).props("outlined")
                        currency_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
                        def validate_currency(e=None):
                            value = currency_select.value or ''
                            if not value.strip() or value == "Please Select":
                                currency_error.text = "Please select the currency."
                                currency_error.style('display:block')
                                currency_select.classes('border border-red-600')
                                return False
                            else:
                                currency_error.text = ''
                                currency_error.style('display:none')
                                currency_select.classes(remove='border border-red-600')
                                return True
                        currency_select.on('blur', validate_currency)
                
                # Row 4 - Department & Initial Fee
                with ui.element('div').classes(f"{row_classes} {std_row_height}"):
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Department").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes + " flex flex-col"):
                        department_select = ui.select(options=["Human Resources", "Finance", "IT", "Operations", "Legal", "Marketing", "Sales", "Customer Service", "Risk Management", "Compliance", "Audit", "Treasury", "Credit", "Retail Banking", "Corporate Banking"], label="Please Select*").classes(input_classes).props("outlined")
                        department_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
                        def validate_department(e=None):
                            value = department_select.value or ''
                            if not value.strip() or value == "Please Select":
                                department_error.text = "Please select the department."
                                department_error.style('display:block')
                                department_select.classes('border border-red-600')
                                return False
                            else:
                                department_error.text = ''
                                department_error.style('display:none')
                                department_select.classes(remove='border border-red-600')
                                return True
                        department_select.on('blur', validate_department)
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Contract Amount").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes + " flex flex-col"):
                        contract_amount_input = ui.input(label="Contract Amount*").classes(input_classes).props("outlined maxlength=20")
                        contract_amount_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
                        
                        def validate_contract_amount(e=None):
                            value = contract_amount_input.value or ''
                            if not value.strip():
                                contract_amount_error.text = "Please enter the Contract Amount"
                                contract_amount_error.style('display:block')
                                contract_amount_input.classes('border border-red-600')
                                return False
                            # Check if value contains only numbers, dots, and commas
                            import re
                            if not re.match(r'^[\d.,]+$', value):
                                contract_amount_error.text = "Please enter only numeric values with . or ,"
                                contract_amount_error.style('display:block')
                                contract_amount_input.classes('border border-red-600')
                                return False
                            contract_amount_error.text = ''
                            contract_amount_error.style('display:none')
                            contract_amount_input.classes(remove='border border-red-600')
                            return True
                        
                        contract_amount_input.on('blur', validate_contract_amount)

                # Row 5 - Contract Start Date & Sub-contractor's name
                with ui.element('div').classes(f"{row_classes} {std_row_height}"):
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Contract Start Date").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        with ui.input('MM/DD/YYYY', value='08/24/2025').classes(input_classes).props("outlined") as start_date:
                            with ui.menu().props('no-parent-event') as start_menu:
                                with ui.date(value='2025-08-24').props('mask=MM/DD/YYYY').bind_value(start_date, 
                                    forward=lambda d: d.replace('-', '/') if d else '', 
                                    backward=lambda d: d.replace('/', '-') if d else ''):
                                    with ui.row().classes('justify-end'):
                                        ui.button('Close', on_click=start_menu.close).props('flat')
                            with start_date.add_slot('append'):
                                ui.icon('edit_calendar').on('click', start_menu.open).classes('cursor-pointer')
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Sub-contractor's name").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes + " flex flex-col"):
                        subcontractor_input = ui.input(label="Sub-contractor's name*").classes(input_classes).props("outlined maxlength=60")
                        subcontractor_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
                        def validate_subcontractor(e=None):
                            value = subcontractor_input.value or ''
                            if not value.strip():
                                subcontractor_error.text = "Please enter the sub-contractor's name."
                                subcontractor_error.style('display:block')
                                subcontractor_input.classes('border border-red-600')
                                return False
                            else:
                                subcontractor_error.text = ''
                                subcontractor_error.style('display:none')
                                subcontractor_input.classes(remove='border border-red-600')
                                return True
                        subcontractor_input.on('blur', validate_subcontractor)
                
                

                # Row 6 - Notify when Expired? (left) & Payment Method (right)
                with ui.element('div').classes(f"{row_classes} {std_row_height}"):
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Notify when Expired?").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes + " flex flex-col"):
                        notify_options = ["Please Select", "Yes", "No"]
                        notify_select = ui.select(options=notify_options, label="Please Select*").classes(input_classes).props("outlined")
                        notify_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
                        def validate_notify(e=None):
                            value = notify_select.value or ''
                            if not value.strip() or value == "Please Select":
                                notify_error.text = "Please select an option."
                                notify_error.style('display:block')
                                notify_select.classes('border border-red-600')
                                return False
                            else:
                                notify_error.text = ''
                                notify_error.style('display:none')
                                notify_select.classes(remove='border border-red-600')
                                return True
                        notify_select.on('blur', validate_notify)
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Payment Method").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes + " flex flex-col"):
                        payment_select = ui.select(options=["Invoice", "Standing Order"], label="Please Select*").classes(input_classes).props("outlined")
                        payment_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
                        def validate_payment(e=None):
                            value = payment_select.value or ''
                            if not value.strip() or value == "Please Select":
                                payment_error.text = "Please select the payment method."
                                payment_error.style('display:block')
                                payment_select.classes('border border-red-600')
                                return False
                            else:
                                payment_error.text = ''
                                payment_error.style('display:none')
                                payment_select.classes(remove='border border-red-600')
                                return True
                        payment_select.on('blur', validate_payment)

                # Row 7 - Contract Manager (left) & Comments (right)
                with ui.element('div').classes(f"{row_classes} {std_row_height}"):
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Contract Manager").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes + " flex flex-col"):
                        contract_manager_options = list(contract_managers_data.keys())
                        contract_manager_select = ui.select(
                            options=contract_manager_options, 
                            value="Please select",
                            label="Contract Manager*"
                        ).classes(input_classes).props("outlined use-input")
                        contract_manager_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
                        
                        def validate_contract_manager(e=None):
                            value = contract_manager_select.value or ''
                            if not value.strip() or value == "Please select":
                                contract_manager_error.text = "Please select a Contract Manager."
                                contract_manager_error.style('display:block')
                                contract_manager_select.classes('border border-red-600')
                                return False
                            else:
                                contract_manager_error.text = ''
                                contract_manager_error.style('display:none')
                                contract_manager_select.classes(remove='border border-red-600')
                                return True
                        
                        contract_manager_select.on('blur', validate_contract_manager)
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Comments").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes + " flex flex-col"):
                        comments_input = ui.input(label="Comments*").classes(input_classes).props("outlined maxlength=100")
                        comments_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
                        def validate_comments(e=None):
                            value = comments_input.value or ''
                            if not value.strip():
                                comments_error.text = "Please enter comments."
                                comments_error.style('display:block')
                                comments_input.classes('border border-red-600')
                                return False
                            else:
                                comments_error.text = ''
                                comments_error.style('display:none')
                                comments_input.classes(remove='border border-red-600')
                                return True
                        comments_input.on('blur', validate_comments)

                # Row 8 - Contract Owner (left) & Attention (right)
                with ui.element('div').classes(f"{row_classes} {std_row_height}"):
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Contract Owner").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes + " flex flex-col"):
                        contract_owner_options = list(contract_managers_data.keys())
                        contract_owner_select = ui.select(
                            options=contract_owner_options, 
                            value="Please select",
                            label="Contract Owner*"
                        ).classes(input_classes).props("outlined use-input")
                        contract_owner_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
                        
                        def validate_contract_owner(e=None):
                            value = contract_owner_select.value or ''
                            if not value.strip() or value == "Please select":
                                contract_owner_error.text = "Please select a person."
                                contract_owner_error.style('display:block')
                                contract_owner_select.classes('border border-red-600')
                                return False
                            else:
                                contract_owner_error.text = ''
                                contract_owner_error.style('display:none')
                                contract_owner_select.classes(remove='border border-red-600')
                                return True
                        
                        contract_owner_select.on('blur', validate_contract_owner)
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Attention").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes + " flex flex-col"):
                        attention_input = ui.input(label="Attention*").classes(input_classes).props("outlined maxlength=100")
                        attention_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
                        def validate_attention(e=None):
                            value = attention_input.value or ''
                            if not value.strip():
                                attention_error.text = "Please enter attention."
                                attention_error.style('display:block')
                                attention_input.classes('border border-red-600')
                                return False
                            else:
                                attention_error.text = ''
                                attention_error.style('display:none')
                                attention_input.classes(remove='border border-red-600')
                                return True
                        attention_input.on('blur', validate_attention)

                # Row 10.2 - Contract Manager (Backup) (left) & Upload Details (right)
                with ui.element('div').classes(f"{row_classes} {std_row_height}"):
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Contract Manager (Backup)").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes + " flex flex-col"):
                        contract_backup_options = list(contract_managers_data.keys())
                        contract_backup_select = ui.select(
                            options=contract_backup_options, 
                            value="Please select",
                            label="Contract Manager (Backup)*"
                        ).classes(input_classes).props("outlined use-input")
                        contract_backup_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
                        
                        def validate_contract_backup(e=None):
                            value = contract_backup_select.value or ''
                            if not value.strip() or value == "Please select":
                                contract_backup_error.text = "Please select a person."
                                contract_backup_error.style('display:block')
                                contract_backup_select.classes('border border-red-600')
                                return False
                            else:
                                contract_backup_error.text = ''
                                contract_backup_error.style('display:none')
                                contract_backup_select.classes(remove='border border-red-600')
                                return True
                        
                        contract_backup_select.on('blur', validate_contract_backup)
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Upload Details").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        upload_details_input = ui.input(label="Description", placeholder="Enter a description for these files").classes(input_classes).props("outlined")
                
                # Row 10.3 - Vendor Contract (left) & Attachments (right)
                with ui.element('div').classes(f"{row_classes} {std_row_height}"):
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Vendor Contract").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes + " flex flex-col py-2 pt-8"):
                        # Storage for uploaded file (matching new_vendor.py pattern) - MUST be before handler
                        vendor_contract_file = {'file': None}
                        
                        # File display and rename section (initially hidden)
                        vendor_contract_file_display = ui.element("div").classes("w-full mt-2 hidden")
                        
                        async def handle_vendor_contract_upload(e):
                            nonlocal vendor_contract_uploaded, vendor_contract_file_name, vendor_contract_rename_input, vendor_contract_date_input
                            
                            # NiceGUI upload event has e.file (async SmallFileUpload object)
                            if not hasattr(e, 'file') or not e.file:
                                ui.notify('No file selected', type='negative')
                                return
                            
                            uploaded_file = e.file
                            file_name = uploaded_file.name if hasattr(uploaded_file, 'name') else 'contract.pdf'
                            
                            # Check file extension - only PDF allowed
                            if not file_name.lower().endswith('.pdf'):
                                ui.notify('Only PDF files are allowed', type='negative')
                                return
                            
                            # Read file content asynchronously (await the coroutine)
                            file_content = await uploaded_file.read()
                            
                            # Store file content as bytes for later upload
                            vendor_contract_file['file'] = file_content
                            vendor_contract_uploaded = True
                            vendor_contract_file_name = file_name
                            
                            # Show file display section
                            vendor_contract_file_display.classes(remove='hidden')
                            vendor_contract_file_display.clear()
                            
                            with vendor_contract_file_display:
                                with ui.card().classes("p-3 bg-blue-50 w-full"):
                                    with ui.row().classes("items-center gap-2 mb-2"):
                                        ui.icon("picture_as_pdf", color="red", size="md")
                                        ui.label(f"File: {file_name}").classes("text-sm font-medium")
                                    
                                    # Rename input with character validation
                                    nonlocal vendor_contract_rename_input
                                    vendor_contract_rename_input = ui.input(
                                        label="Rename Document*",
                                        value=file_name.replace('.pdf', ''),
                                        placeholder="Enter document name (letters, numbers, -, |, & only)"
                                    ).classes(input_classes + " mb-2").props("outlined")
                                    
                                    # Add validation on input change
                                    def validate_rename_input(e):
                                        import re
                                        value = vendor_contract_rename_input.value or ''
                                        if value and not re.match(r'^[a-zA-Z0-9\s\-\|&]*$', value):
                                            # Remove invalid characters
                                            cleaned = re.sub(r'[^a-zA-Z0-9\s\-\|&]', '', value)
                                            vendor_contract_rename_input.value = cleaned
                                            ui.notify('Only letters, numbers, and special characters (-, |, &) are allowed', type='warning')
                                    
                                    vendor_contract_rename_input.on('input', validate_rename_input)
                                    
                                    # Date signed input with calendar
                                    nonlocal vendor_contract_date_input
                                    with ui.input('MM/DD/YYYY', placeholder='Document Date Signed*').classes(input_classes).props("outlined") as vendor_contract_date_input:
                                        with ui.menu().props('no-parent-event') as vendor_contract_date_menu:
                                            with ui.date().props('mask=MM/DD/YYYY').bind_value(vendor_contract_date_input, 
                                                forward=lambda d: d.replace('-', '/') if d else '', 
                                                backward=lambda d: d.replace('/', '-') if d else ''):
                                                with ui.row().classes('justify-end'):
                                                    ui.button('Close', on_click=vendor_contract_date_menu.close).props('flat')
                                        with vendor_contract_date_input.add_slot('append'):
                                            ui.icon('edit_calendar').on('click', vendor_contract_date_menu.open).classes('cursor-pointer')
                            
                            vendor_contract_error.text = ''
                            vendor_contract_error.style('display:none')
                            vendor_contract_upload.classes(remove='border border-red-600')
                            ui.notify('PDF file uploaded successfully', type='positive')
                        
                        # Upload component with auto_upload enabled
                        vendor_contract_upload = ui.upload(
                            on_upload=handle_vendor_contract_upload,
                            auto_upload=True,
                            label="Drop PDF file here or click to browse*"
                        ).props('accept=.pdf color=primary outlined').classes("w-full")
                        
                        vendor_contract_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
                        
                        def validate_vendor_contract(_e=None):
                            nonlocal vendor_contract_uploaded, vendor_contract_file_name, vendor_contract_rename_input, vendor_contract_date_input
                            if not vendor_contract_uploaded or not vendor_contract_file_name:
                                vendor_contract_error.text = "Please upload this required document"
                                vendor_contract_error.style('display:block')
                                vendor_contract_upload.classes('border border-red-600')
                                return False
                            
                            # Validate rename input (only letters, numbers, -, |, &)
                            if vendor_contract_rename_input:
                                rename_value = vendor_contract_rename_input.value or ''
                                import re
                                if not rename_value.strip():
                                    vendor_contract_error.text = "Please enter a document name"
                                    vendor_contract_error.style('display:block')
                                    vendor_contract_rename_input.classes('border border-red-600')
                                    return False
                                # Check for allowed characters: letters, numbers, -, |, &
                                if not re.match(r'^[a-zA-Z0-9\s\-\|&]+$', rename_value):
                                    vendor_contract_error.text = "Document name can only contain letters, numbers, and special characters: -, |, &"
                                    vendor_contract_error.style('display:block')
                                    vendor_contract_rename_input.classes('border border-red-600')
                                    return False
                                vendor_contract_rename_input.classes(remove='border border-red-600')
                            
                            # Validate date signed
                            if vendor_contract_date_input:
                                date_value = vendor_contract_date_input.value or ''
                                if not date_value.strip():
                                    vendor_contract_error.text = "Please enter the document date signed"
                                    vendor_contract_error.style('display:block')
                                    vendor_contract_date_input.classes('border border-red-600')
                                    return False
                                vendor_contract_date_input.classes(remove='border border-red-600')
                            
                            vendor_contract_error.text = ''
                            vendor_contract_error.style('display:none')
                            vendor_contract_upload.classes(remove='border border-red-600')
                            return True
                    
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Attachments").classes(label_classes)
                    with ui.element('div').classes(f"{input_cell_classes} pt-4 pb-0"):
                        uploaded_files_container = ui.element("div").classes("flex flex-col gap-1 mb-2")
                        with ui.card().classes("w-full h-auto p-0 mt-4"):
                            
                            async def handle_upload(e):
                                # NiceGUI upload event has e.file (async SmallFileUpload object)
                                if hasattr(e, 'file') and e.file:
                                    uploaded_file = e.file
                                    file_name = uploaded_file.name if hasattr(uploaded_file, 'name') else 'attachment'
                                    
                                    # Read file content asynchronously
                                    await uploaded_file.read()
                                    
                                    with uploaded_files_container:
                                        with ui.card().classes("p-1 bg-blue-50 flex gap-1 items-center"):
                                            ui.icon("attach_file", size="xs").classes("text-[#144c8e]")
                                            ui.label(file_name).classes("text-xs")
                                            ui.icon("close", size="xs").classes("cursor-pointer text-gray-500 hover:text-red-500")
                                    
                                    ui.notify(f'File uploaded: {file_name}', type='positive')
                                else:
                                    ui.notify('No file uploaded', type='negative')
                            
                            ui.upload(on_upload=handle_upload, auto_upload=True, multiple=False, label="Drop files here or click to browse").props('accept=*/* color=primary outlined').classes("w-full")

                # Add Submit and Cancel buttons at the bottom
                with ui.element("div").classes("flex justify-end gap-4 mt-8 mr-20 w-full").props(f'id="c225"'):
                    def clear_contract_form():
                        """Reset all contract form fields to their defaults"""
                        nonlocal vendor_contract_uploaded, vendor_contract_file_name
                        vendor_select.value = vendor_names[0] if vendor_names else None
                        desc_input.value = ""
                        termination_input.value = "30"
                        expiration_input.value = "30"
                        auto_renewal_select.value = "Please select"
                        renewal_period_select.value = "Please select"
                        renewal_period_select.set_visibility(False)
                        contract_type_select.value = None
                        currency_select.value = None
                        department_select.value = None
                        contract_amount_input.value = ""
                        start_date.value = "08/24/2025"
                        end_date.value = "08/24/2025"
                        subcontractor_input.value = ""
                        payment_select.value = None
                        comments_input.value = ""
                        notify_select.value = None
                        attention_input.value = ""
                        contract_manager_select.value = "Please select"
                        contract_owner_select.value = "Please select"
                        contract_backup_select.value = "Please select"
                        upload_details_input.value = ""
                        vendor_contract_uploaded = False
                        vendor_contract_file_name = None
                        vendor_contract_file_display.classes(add='hidden')
                        vendor_contract_file['file'] = None
                        ui.notify('✨ Form cleared', type='info')
                    
                    ui.button("Cancel", icon="close", on_click=clear_contract_form).props("flat").classes("text-gray-700")
                    async def submit_contract():
                        validations = [
                            validate_vendor(),
                            validate_desc(),
                            validate_termination(),
                            validate_auto_renewal(),
                            validate_expiration(),
                            validate_contract_type(),
                            validate_currency(),
                            validate_department(),
                            validate_contract_amount(),
                            validate_subcontractor(),
                            validate_payment(),
                            validate_comments(),
                            validate_notify(),
                            validate_attention(),
                            validate_contract_manager(),
                            validate_contract_owner(),
                            validate_contract_backup(),
                            validate_vendor_contract()
                        ]
                        if not all(validations):
                            ui.notify('Please fix all required fields before submitting.', type='negative')
                            return
                        # Collect all field values and prepare for API
                        # Convert dates from MM/DD/YYYY to YYYY-MM-DD format
                        def convert_date(date_str):
                            if not date_str:
                                return None
                            try:
                                # If format is MM/DD/YYYY, convert to YYYY-MM-DD
                                if '/' in date_str:
                                    month, day, year = date_str.split('/')
                                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                                return date_str
                            except:
                                return None
                        
                        # Map vendor name to ID
                        selected_vendor = vendor_select.value
                        vendor_id = vendor_options.get(selected_vendor, 1)
                        
                        # Map manager names to user IDs (use first two users as fallback)
                        owner_name = contract_owner_select.value
                        backup_name = contract_backup_select.value
                        owner_id = users_map.get(owner_name, 1)
                        backup_id = users_map.get(backup_name, 2)
                        
                        # Validate dates
                        start = convert_date(start_date.value)
                        end = convert_date(end_date.value)
                        
                        if start and end and start >= end:
                            ui.notify('Contract end date must be after start date', type='negative')
                            return
                        
                        # Map contract manager to user ID
                        manager_name = contract_manager_select.value
                        manager_id = users_map.get(manager_name, 3)  # Default to user 3 if not found
                        
                        # Ensure manager is different from owner
                        if manager_id == owner_id:
                            # Use backup as manager if manager same as owner
                            manager_id = backup_id
                        
                        # Prepare contract data matching the API schema
                        contract_data = {
                            "vendor_id": vendor_id,
                            "contract_type": contract_type_select.value,
                            "contract_description": desc_input.value,
                            "start_date": start,
                            "end_date": end,
                            "contract_amount": float(contract_amount_input.value.replace(',', '')),
                            "contract_currency": currency_select.value,
                            "department": department_select.value,
                            "payment_method": payment_select.value,
                            "termination_notice_period": f"{termination_input.value} days",
                            "expiration_notice_frequency": f"{expiration_input.value} days",
                            "automatic_renewal": auto_renewal_select.value,
                            "renewal_period": renewal_period_select.value if auto_renewal_select.value == "Yes" else None,
                            "contract_owner_id": owner_id,
                            "contract_owner_backup_id": backup_id,
                            "contract_owner_manager_id": manager_id
                        }
                        
                        # Prepare form data for API (matching vendors pattern)
                        api_host = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
                        url = f"{api_host}{settings.api_v1_prefix}/contracts/"
                        
                        # Get uploaded file content
                        if not vendor_contract_uploaded:
                            ui.notify('Please upload the vendor contract document', type='negative')
                            return
                        
                        # Get document name and date
                        doc_name = vendor_contract_rename_input.value if vendor_contract_rename_input else vendor_contract_file_name
                        doc_date = convert_date(vendor_contract_date_input.value) if vendor_contract_date_input else None
                        
                        if not doc_date:
                            ui.notify('Please enter the document signed date', type='negative')
                            return
                        
                        # Prepare multipart form data (matching new_vendor.py pattern)
                        files = {
                            'contract_data': (None, json.dumps(contract_data)),
                            'document_name': (None, doc_name),
                            'document_signed_date': (None, doc_date)
                        }
                        
                        # Add the uploaded PDF file
                        if vendor_contract_file.get('file'):
                            files['contract_document'] = ('contract.pdf', vendor_contract_file['file'], 'application/pdf')
                        else:
                            ui.notify('Error: Contract document not properly uploaded. Please re-upload the file.', type='negative')
                            return
                        
                        # Send to backend API
                        try:
                            print(f"\n{'='*60}")
                            print(f"SUBMITTING CONTRACT TO API")
                            print(f"{'='*60}")
                            print(f"Sending contract to API: {url}")
                            print(f"Contract data: {json.dumps(contract_data, indent=2)}")
                            print(f"{'='*60}\n")
                            
                            async with httpx.AsyncClient(timeout=30.0) as client:
                                response = await client.post(url, files=files)
                                
                                print(f"\n{'='*60}")
                                print(f"API RESPONSE")
                                print(f"{'='*60}")
                                print(f"Status Code: {response.status_code}")
                                print(f"Response Body: {response.text[:500]}")
                                print(f"{'='*60}\n")
                                
                                if response.status_code == 201:
                                    result = response.json()
                                    contract_id = result.get("contract_id", "N/A")
                                    vendor_name = result.get("vendor_name", "N/A")
                                    ui.notify(
                                        f'✅ SUCCESS! Contract "{contract_id}" created successfully!',
                                        type='positive',
                                        position='top',
                                        close_button=True,
                                        timeout=5000
                                    )
                                    print(f"✅ Contract created: {contract_id}")
                                    # Clear the form after successful submission
                                    clear_contract_form()
                                    # Optionally navigate to active contracts page
                                    # ui.navigate.to('/active-contracts')
                                else:
                                    error_text = ""
                                    try:
                                        error_json = response.json()
                                        if 'detail' in error_json:
                                            detail = error_json['detail']
                                            if 'validation error' in str(detail).lower():
                                                # Extract key error messages
                                                error_lines = str(detail).split('\n')
                                                error_text = '\n'.join([line for line in error_lines if line.strip() and 'For further information' not in line])
                                            else:
                                                error_text = str(detail)
                                        else:
                                            error_text = str(error_json)
                                    except:
                                        error_text = response.text[:300]
                                    
                                    print(f"❌ Error creating contract: {error_text}")
                                    ui.notify(f'❌ Error: {error_text}', type='negative', close_button=True, timeout=15000)
                                    
                        except httpx.TimeoutException:
                            print(f"❌ Request timeout")
                            ui.notify('⏱️ Request timed out. Please try again.', type='negative')
                        except httpx.ConnectError as e:
                            print(f"❌ Connection error: {e}")
                            ui.notify('🔌 Connection error: Cannot reach the server', type='negative')
                        except Exception as e:
                            print(f"❌ Unexpected error: {type(e).__name__}: {e}")
                            import traceback
                            traceback.print_exc()
                            ui.notify(f'❌ Unexpected error: {str(e)}', type='negative')
                    ui.button("Submit", icon="check", on_click=submit_contract).classes("bg-[#144c8e] text-white")
            
           