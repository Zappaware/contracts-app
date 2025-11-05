from nicegui import ui


def new_contract():
    with ui.element("div").classes(
        "flex flex-col items-center justify-center mt-8 w-full "
    ):
        vendors = [
            # fake vendor names
            "Transportation Co.",
            "Logistics Ltd.",
            "Freight Masters",
            "Cargo Solutions",
            "Transit Experts",
        ]
        vendor_select = ui.select(options=vendors, value=vendors[0], label="Select vendor*").classes(
            "w-64 mt-8 font-[segoe ui]"
        ).props("outlined")
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
        with ui.element("div").classes("w-full border rounded border-gray-300 max-w-7xl mt-8 p-6 mx-auto"):
            # Define style classes as constants to avoid duplication
            label_classes = "text-white font-[segoe ui] py-2 px-4 h-full flex items-center"
            input_classes = "w-full font-[segoe ui]"
            row_classes = "flex w-full"
            std_row_height = "h-auto"

            # Cell classes for consistent styling
            label_cell_classes = "bg-[#144c8e] w-[16.6%] flex items-center"
            input_cell_classes = "bg-white p-2 w-[33.3%]"
            
            # Create a custom table-like layout using divs
            with ui.element("div").classes("w-full border-collapse flex flex-col"):
                
                # Row 1 - ID & Termination Notice
                with ui.element('div').classes(f"{row_classes} {std_row_height}"):
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("ID").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        ui.label("ID").classes(input_classes)
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
                
                # Row 2 - Automatic Renewal & Expiration Reminder Notice
                with ui.element('div').classes(f"{row_classes} {std_row_height}"):
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Automatic Renewal").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes + " flex flex-col"):
                        auto_renewal_options = ["Please Select", "Yes", "No"]
                        auto_renewal_select = ui.select(options=auto_renewal_options, label="Please Select*").classes(input_classes).props("outlined")
                        auto_renewal_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
                        def validate_auto_renewal(e=None):
                            value = auto_renewal_select.value or ''
                            if not value.strip() or value == "Please Select":
                                auto_renewal_error.text = "Please indicate if there is an automatic renewal period in place"
                                auto_renewal_error.style('display:block')
                                auto_renewal_select.classes('border border-red-600')
                                return False
                            else:
                                auto_renewal_error.text = ''
                                auto_renewal_error.style('display:none')
                                auto_renewal_select.classes(remove='border border-red-600')
                                return True
                        auto_renewal_select.on('blur', validate_auto_renewal)
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Expiration Reminder Notice").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes + " flex flex-col"):
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
                
                # Row 2.5 - Renewal Period (conditional display)
                renewal_period_row = ui.element('div').classes(f"{row_classes} {std_row_height}").style('display:none')
                with renewal_period_row:
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Renewal Period").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes + " flex flex-col"):
                        renewal_period_options = ["Please Select", "1 Year", "2 Years", "3 Years"]
                        renewal_period_select = ui.select(options=renewal_period_options, label="Please Select").classes(input_classes).props("outlined")
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        ui.label("").classes(input_classes)
                
                # Handle showing/hiding renewal period field
                def handle_renewal_change(e):
                    if auto_renewal_select.value == "Yes":
                        renewal_period_row.style('display:flex')
                    else:
                        renewal_period_row.style('display:none')
                        renewal_period_select.value = "Please Select"
                
                auto_renewal_select.on('change', handle_renewal_change)
                
                # Row 3 - Type of Contract & Currency
                with ui.element('div').classes(f"{row_classes} {std_row_height}"):
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Type of Contract").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes + " flex flex-col"):
                        contract_type_select = ui.select(options=["Hardware", "Software", "Building", "Airco", "Custody Service", "Elevator", "Services", "Other", "Generator", "Certification", "Security", "Price List", "Service Agreement", "Non-Disclosure Agreement", "Terms & Conditions", "Consultancy", "Maintenance", "Proposal", "Advertising", "Termination", "Letter of Intent", "Service & Maintenance", "Lease Agreement", "Job Affirmation", "Legal Services", "Insurance", "Draft", "ATM - Lease Agreement", "Standing Order", "License Agreement", "Letter of Engagement", "Security Agreement", "Agreement", "Concession", "Membership Agreement", "Erfpacht", "Subscription", "Membership", "APPRAISAL", "Sponsorship", "Agency Agreement", "Preventative Service Plan", "Registration", "Quotation", "Statement Of Work"], label="Please Select*").classes(input_classes).props("outlined")
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
                        currency_select = ui.select(options=["USD", "EUR", "GBP", "JPY", "CAD"], label="Please Select*").classes(input_classes).props("outlined")
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
                        department_select = ui.select(options=["IT - Operations", "Compliance Department", "Finance", "Internal Audit", "Human Resources", "Executive Office", "Insurance Department", "Premises & Facilities", "Marketing Department", "Payment Operations", "Retail Banking", "Payment Strategy & Solutions", "CARC", "Corporate Banking - Mid Office", "Security Department", "Management Team", "Special Assets", "Contact Center", "Corporate Banking - Corporate Credit", "Credit Risk", "Archiving Services", "Project Management Team", "IT - Projects", "KYC Due Diligence", "PBIO", "ORCO Group N.V.", "Business Continuity Management", "Management Board", "Integrity", "Platinum Banking", "OBAB IT", "OBAB Security", "OBAB Retail", "OBAB PBIO", "OBAB Payment Strategy & Solutions", "OBAB Payment Operations", "OBAB Premises & Facilities", "OBAB Internal Audit"], label="Please Select*").classes(input_classes).props("outlined")
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
                
                # Row 6 - Contract Expiration Date & Maintenance Fee
                with ui.element('div').classes(f"{row_classes} {std_row_height}"):
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
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Maintenance Fee").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes + " flex flex-col"):
                        maintenance_fee_input = ui.input(label="Do not Format it*", value="0.00").props("outlined disable maxlength=10").classes(input_classes)
                        maintenance_fee_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
                        def validate_maintenance_fee(e=None):
                            value = maintenance_fee_input.value or ''
                            if not value.strip():
                                maintenance_fee_error.text = "Please enter the maintenance fee."
                                maintenance_fee_error.style('display:block')
                                maintenance_fee_input.classes('border border-red-600')
                                return False
                            else:
                                maintenance_fee_error.text = ''
                                maintenance_fee_error.style('display:none')
                                maintenance_fee_input.classes(remove='border border-red-600')
                                return True
                        maintenance_fee_input.on('blur', validate_maintenance_fee)

                # Row 7 - Contract Termination & Payment Method
                with ui.element('div').classes(f"{row_classes} {std_row_height}"):
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Contract Termination").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        with ui.element("div").classes("py-1"):
                            ui.switch("Yes")
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Payment Method").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes + " flex flex-col"):
                        payment_select = ui.select(options=["Credit Card", "Bank Transfer", "Cash", "Check"], label="Please Select*").classes(input_classes).props("outlined")
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

                # Row 8 - Maintenance Terms & Comments
                with ui.element('div').classes(f"{row_classes} {std_row_height}"):
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Maintenance Terms").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes + " flex flex-col"):
                        maintenance_terms_options = [
                            "Please Select",
                            "Annual Service",
                            "Monthly Checkup",
                            "On Demand",
                            "Full Coverage",
                            "Limited Warranty"
                        ]
                        maintenance_terms_select = ui.select(options=maintenance_terms_options, label="Please Select*").classes(input_classes).props("outlined")
                        maintenance_terms_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
                        def validate_maintenance_terms(e=None):
                            value = maintenance_terms_select.value or ''
                            if not value.strip() or value == "Please Select":
                                maintenance_terms_error.text = "Please select the maintenance terms."
                                maintenance_terms_error.style('display:block')
                                maintenance_terms_select.classes('border border-red-600')
                                return False
                            else:
                                maintenance_terms_error.text = ''
                                maintenance_terms_error.style('display:none')
                                maintenance_terms_select.classes(remove='border border-red-600')
                                return True
                        maintenance_terms_select.on('blur', validate_maintenance_terms)
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

                # Row 9 - Notify when Expired? & Attention
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

                # Row 10 - Notification Email Address & Last Revision User
                with ui.element('div').classes(f"{row_classes} {std_row_height}"):
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Notification Email Address").classes(label_classes).props("outlined")
                    with ui.element('div').classes(input_cell_classes + " flex flex-col"):
                        email_chips = ui.input_chips("Enter email and press Enter", new_value_mode="add").classes(input_classes).props("type=email outlined chips")
                        email_chips_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
                        def validate_email_chips(e=None):
                            values = email_chips.value or []
                            if not values or not all('@' in v and '.' in v for v in values):
                                email_chips_error.text = "Please enter valid email addresses."
                                email_chips_error.style('display:block')
                                email_chips.classes('border border-red-600')
                                return False
                            else:
                                email_chips_error.text = ''
                                email_chips_error.style('display:none')
                                email_chips.classes(remove='border border-red-600')
                                return True
                        email_chips.on('blur', validate_email_chips)
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Last Revision User").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes + " flex flex-col"):
                        revision_user_input = ui.input(label="Last Revision User*").classes(input_classes).props("outlined maxlength=60")
                        revision_user_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
                        def validate_revision_user(e=None):
                            value = revision_user_input.value or ''
                            if not value.strip():
                                revision_user_error.text = "Please enter the last revision user."
                                revision_user_error.style('display:block')
                                revision_user_input.classes('border border-red-600')
                                return False
                            else:
                                revision_user_error.text = ''
                                revision_user_error.style('display:none')
                                revision_user_input.classes(remove='border border-red-600')
                                return True
                        revision_user_input.on('blur', validate_revision_user)
                
                # Row 10.5 - File Attachments (right below Notification Email Address)
                with ui.element('div').classes(f"{row_classes} {std_row_height}"):
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Attachments").classes("text-white font-[segoe ui] py-8 px-4 h-full")
                    with ui.element('div').classes(f"{input_cell_classes} pt-4 pb-0"):
                        with ui.card().classes("w-full h-auto p-0 mt-4"):
                            
                            def handle_upload(e):
                                for file_name in e.file_names:
                                    with uploaded_files_container:
                                        with ui.card().classes("p-1 bg-blue-50 flex gap-1 items-center"):
                                            ui.icon("attach_file", size="xs").classes("text-[#144c8e]")
                                            ui.label(file_name).classes("text-xs")
                                            ui.icon("close", size="xs").classes("cursor-pointer text-gray-500 hover:text-red-500")
                                ui.notify(f'{len(e.file_names)} file(s) uploaded successfully', type='positive')
                            
                            ui.upload(on_upload=handle_upload, multiple=True, label="Drop files here or click to browse").props('accept=*/* color=primary outlined').classes("w-full")
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Upload Details").classes("text-white font-[segoe ui] py-8 px-4  h-full")
                    with ui.element('div').classes(input_cell_classes):
                        ui.input(label="Description", placeholder="Enter a description for these files").classes(input_classes).props("outlined")
                
                # Row 11 - Empty & Last Revision Date
                with ui.element('div').classes(f"{row_classes} {std_row_height}"):
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        ui.label("").classes(input_classes)
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Last Revision Date").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        ui.input().classes(input_classes).props("outlined")


                # Add Submit and Cancel buttons at the bottom
                with ui.element("div").classes("flex justify-end gap-4 mt-8 mr-20 w-full"):
                    ui.button("Cancel", icon="close").props("flat").classes("text-gray-700")
                    def submit_contract():
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
                            validate_maintenance_fee(),
                            validate_payment(),
                            validate_maintenance_terms(),
                            validate_comments(),
                            validate_notify(),
                            validate_attention(),
                            validate_email_chips(),
                            validate_revision_user()
                        ]
                        if not all(validations):
                            ui.notify('Please fix all required fields before submitting.', type='negative')
                            return
                        # Collect all field values
                        data = {
                            'vendor': vendor_select.value,
                            'description': desc_input.value,
                            'termination_notice': termination_input.value,
                            'automatic_renewal': auto_renewal_select.value,
                            'renewal_period': renewal_period_select.value if auto_renewal_select.value == "Yes" else None,
                            'expiration_reminder': expiration_input.value,
                            'contract_type': contract_type_select.value,
                            'currency': currency_select.value,
                            'department': department_select.value,
                            'contract_amount': contract_amount_input.value,
                            'subcontractor': subcontractor_input.value,
                            'maintenance_fee': maintenance_fee_input.value,
                            'payment_method': payment_select.value,
                            'maintenance_terms': maintenance_terms_select.value,
                            'comments': comments_input.value,
                            'notify_when_expired': notify_select.value,
                            'attention': attention_input.value,
                            'notification_emails': email_chips.value,
                            'last_revision_user': revision_user_input.value
                        }
                        ui.notify('Contract submitted successfully!', type='positive')
                        # Here you can add code to send 'data' to your backend or API
                    ui.button("Submit", icon="check", on_click=submit_contract).classes("bg-[#144c8e] text-white")
            
           