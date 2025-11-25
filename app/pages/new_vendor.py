from nicegui import ui
import requests
import json

def get_country_list():
    try:
        response = requests.get('https://restcountries.com/v3.1/all?fields=name', timeout=5)
        response.raise_for_status()
        countries = sorted([c['name']['common'] for c in response.json()])
        return ["Please select"] + countries
    except Exception:
        # fallback in case of error
        return ["Please select", "United States", "Canada", "Mexico"]


def new_vendor():
            
    with ui.element("div").classes(
        "flex flex-col items-center justify-center mt-8 w-full "
    ):
        ui.input(label="Vendor search", placeholder="Search for existing vendors...").classes("w-1/2 mt-4 font-[segoe ui]").props("outlined")
        ui.button("New Vendor", icon="add").classes("mt-4 bg-[#144c8e] text-white")
        
        # Add vendor details section as a div-based table with 4 columns
    with ui.element("div").classes("w-full border rounded border-gray-300 max-w-7xl mt-8 p-6 mx-auto flex flex-col min-h-[600px] h-auto bg-white overflow-auto"):
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
                
                # Row 1 - ID & AB Customer?
                with ui.element('div').classes(f"{row_classes} {std_row_height}"):
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("ID").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        ui.label("ID").classes(input_classes)
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("AB Customer?").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes + " flex flex-col min-h-[70px]"):
                        ab_options = ["Please select", "Yes", "No"]
                        ab_select = ui.select(
                            options=ab_options,
                            value="Please select",
                            label="AB Customer?*"
                        ).classes("w-full font-[segoe ui]").props("outlined use-input")
                        ab_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')

                        def validate_ab_customer(e=None):
                            value = ab_select.value
                            if value == "Please select" or not value:
                                ab_error.text = "Please indicate if vendor is an AB Customer"
                                ab_error.style('display:block')
                                ab_select.classes('border border-red-600')
                                return False
                            else:
                                ab_error.text = ''
                                ab_error.style('display:none')
                                ab_select.classes(remove='border border-red-600')
                                return True

                        ab_select.on('blur', validate_ab_customer)
                # Row X - Material Outsourcing Arrangement? and Bank Customer
                with ui.element('div').classes(f"{row_classes} {std_row_height}"):
                    # Blue column with label
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Material Outsourcing Arrangement?").classes(label_classes)
                    # Column 2: Switch and validation
                    with ui.element('div').classes(input_cell_classes + " flex flex-col min-h-[70px]"):
                        moa_options = ["Please select", "Yes", "No"]
                        moa_select = ui.select(
                            options=moa_options,
                            value="Please select",
                            label="Material Outsourcing Arrangement?*"
                        ).classes("w-full font-[segoe ui]").props("outlined use-input")
                        moa_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')

                        def validate_moa(e=None):
                            value = moa_select.value
                            if value == "Please select" or not value:
                                moa_error.text = "Please indicate if vendor is considered material outsourcing arrangement"
                                moa_error.style('display:block')
                                moa_select.classes('border border-red-600')
                                return False
                            else:
                                moa_error.text = ''
                                moa_error.style('display:none')
                                moa_select.classes(remove='border border-red-600')
                                return True

                        moa_select.on('blur', validate_moa)
                    # Column 3: Bank Customer dropdown and conditional CIF field
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Bank Customer").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes + " flex flex-col min-h-[70px]"):
                        bank_options = ["Please select", "Aruba Bank", "Orco Bank", "None"]
                        bank_select = ui.select(
                            options=bank_options,
                            value="Please select",
                            label="Bank Customer*"
                        ).classes("w-full font-[segoe ui]").props("outlined use-input")
                        bank_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')

                        cif_input = ui.input(label="CIF*", placeholder="Enter CIF...").classes("w-full font-[segoe ui] mt-2").props("outlined maxlength=6")
                        cif_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
                        cif_input.set_visibility(False)

                        def validate_bank(e=None):
                            value = bank_select.value
                            if value == "Please select" or not value:
                                bank_error.text = "Please provide the required information."
                                bank_error.style('display:block')
                                bank_select.classes('border border-red-600')
                                cif_input.set_visibility(False)
                                return False
                            else:
                                bank_error.text = ''
                                bank_error.style('display:none')
                                bank_select.classes(remove='border border-red-600')
                                if value in ["Aruba Bank", "Orco Bank"]:
                                    cif_input.set_visibility(True)
                                    cif_val = cif_input.value or ''
                                    if not cif_val.isdigit() or len(cif_val) != 6:
                                        cif_error.text = "Please provide a valid 6-digit CIF."
                                        cif_error.style('display:block')
                                        cif_input.classes('border border-red-600')
                                        return False
                                    else:
                                        cif_error.text = ''
                                        cif_error.style('display:none')
                                        cif_input.classes(remove='border border-red-600')
                                        return True
                                else:
                                    cif_input.set_visibility(False)
                                    cif_error.text = ''
                                    cif_error.style('display:none')
                                    cif_input.classes(remove='border border-red-600')
                                    return True

                        bank_select.on('blur', validate_bank)
                        cif_input.on('blur', validate_bank)
                        bank_error
                        cif_input
                        cif_error
                    
                    # ...existing code...

                # Row 2 - Name & Contact Person
                with ui.element('div').classes(f"{row_classes} {std_row_height}"):
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Name").classes(label_classes)
                    # Vendor Name field with validation (already implemented)
                    with ui.element('div').classes(input_cell_classes + " flex flex-col justify-center min-h-[70px]"):
                        vendor_name_input = ui.input(label="Vendor Name*", placeholder="Enter vendor name...").classes("w-full font-[segoe ui]").props("outlined maxlength=60")
                        vendor_name_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')

                        def validate_vendor_name(e=None):
                            value = vendor_name_input.value or ''
                            if not value.strip():
                                vendor_name_error.text = "Please enter the Vendor Name"
                                vendor_name_error.style('display:block')
                                vendor_name_input.classes('border border-red-600')
                                return False
                            else:
                                vendor_name_error.text = ''
                                vendor_name_error.style('display:none')
                                vendor_name_input.classes(remove='border border-red-600')
                                return True
                        vendor_name_input.on('blur', validate_vendor_name)

                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Contact Person").classes(label_classes)
                    # Vendor Contact Person field with validation
                    with ui.element('div').classes(input_cell_classes + " flex flex-col justify-center min-h-[70px]"):
                        contact_person_input = ui.input(label="Vendor Contact Person*", placeholder="Enter contact person...").classes("w-full font-[segoe ui]").props("outlined maxlength=60")
                        contact_person_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')

                        def validate_contact_person(e=None):
                            value = contact_person_input.value or ''
                            if not value.strip():
                                contact_person_error.text = "Please enter the vendor contact person."
                                contact_person_error.style('display:block')
                                contact_person_input.classes('border border-red-600')
                                return False
                            else:
                                contact_person_error.text = ''
                                contact_person_error.style('display:none')
                                contact_person_input.classes(remove='border border-red-600')
                                return True
                        contact_person_input.on('blur', validate_contact_person)
                
                # Row 3 - Address 1 & Address 2 (with validation)
                with ui.element('div').classes(f"{row_classes} {std_row_height}"):
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Address 1").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes + " flex flex-col"):
                        address1_input = ui.input(label="Address 1*", placeholder="Enter address...").classes(input_classes).props("outlined maxlength=60")
                        address1_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
                        def validate_address1(e=None):
                            value = address1_input.value or ''
                            if not value.strip():
                                address1_error.text = "Please enter Address 1."
                                address1_error.style('display:block')
                                address1_input.classes('border border-red-600')
                                return False
                            else:
                                address1_error.text = ''
                                address1_error.style('display:none')
                                address1_input.classes(remove='border border-red-600')
                                return True
                        address1_input.on('blur', validate_address1)
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Address 2").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes + " flex flex-col"):
                        address2_input = ui.input(label="Address 2*", placeholder="Enter address...").classes(input_classes).props("outlined maxlength=60")
                        address2_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
                        def validate_address2(e=None):
                            value = address2_input.value or ''
                            if not value.strip():
                                address2_error.text = "Please enter Address 2."
                                address2_error.style('display:block')
                                address2_input.classes('border border-red-600')
                                return False
                            else:
                                address2_error.text = ''
                                address2_error.style('display:none')
                                address2_input.classes(remove='border border-red-600')
                                return True
                        address2_input.on('blur', validate_address2)

                # Row 4 - City & State (with validation)
                with ui.element('div').classes(f"{row_classes} {std_row_height}"):
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("City").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes + " flex flex-col"):
                        city_input = ui.input(label="City*", placeholder="Enter city...").classes(input_classes).props("outlined maxlength=30")
                        city_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
                        def validate_city(e=None):
                            value = city_input.value or ''
                            if not value.strip():
                                city_error.text = "Please enter the city."
                                city_error.style('display:block')
                                city_input.classes('border border-red-600')
                                return False
                            else:
                                city_error.text = ''
                                city_error.style('display:none')
                                city_input.classes(remove='border border-red-600')
                                return True
                        city_input.on('blur', validate_city)
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("State").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes + " flex flex-col"):
                        state_input = ui.input(label="State*", placeholder="Enter state...").classes(input_classes).props("outlined maxlength=30")
                        state_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
                        def validate_state(e=None):
                            value = state_input.value or ''
                            if not value.strip():
                                state_error.text = "Please enter the state."
                                state_error.style('display:block')
                                state_input.classes('border border-red-600')
                                return False
                            else:
                                state_error.text = ''
                                state_error.style('display:none')
                                state_input.classes(remove='border border-red-600')
                                return True
                        state_input.on('blur', validate_state)

                # Row 5 - Zip Code & Country (with validation)
            with ui.element('div').classes("flex w-full h-16"):
                with ui.element('div').classes("bg-[#144c8e] w-[16.6%] flex items-center"):
                    ui.label("Zip Code").classes("text-white font-[segoe ui] py-2 px-4 h-full flex items-center")
                with ui.element('div').classes("bg-white p-2 w-[33.3%]"):
                    zip_input = ui.input(label="Zip Code*", placeholder="Enter zip code...").classes("w-full font-[segoe ui]").props("outlined maxlength=10")
                    zip_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
                    def validate_zip(e=None):
                        value = zip_input.value or ''
                        if not value.strip():
                            zip_error.text = "Please enter the zip code."
                            zip_error.style('display:block')
                            zip_input.classes('border border-red-600')
                            return False
                        else:
                            zip_error.text = ''
                            zip_error.style('display:none')
                            zip_input.classes(remove='border border-red-600')
                            return True
                    zip_input.on('blur', validate_zip)
                with ui.element('div').classes("bg-[#144c8e] w-[16.6%] flex items-center"):
                    ui.label("Country").classes("text-white font-[segoe ui] py-2 px-4 h-full flex items-center")
                with ui.element('div').classes("bg-white p-2 w-[33.3%]"):
                    country_options = get_country_list()
                    country_error = ui.label('').classes('text-red-600 text-sm mb-2').style('display:none')
                    country_select = ui.select(
                        options=country_options,
                        value="Please select",
                        label="Vendor Country*"
                    ).classes("w-full font-[segoe ui]").props("outlined use-input")

                    def validate_country(e=None):
                        value = country_select.value
                        if value == "Please select" or not value:
                            country_error.text = "Please select the vendor country."
                            country_error.style('display:block')
                            country_select.classes('border border-red-600')
                            return False
                        else:
                            country_error.text = ''
                            country_error.style('display:none')
                            country_select.classes(remove='border border-red-600')
                            return True
                    country_select.on('blur', validate_country)
                
                # Row 6 - Telephone Number & Email
                with ui.element('div').classes(f"{row_classes} {std_row_height}"):
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Telephone Number").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        phone_input = ui.input(label="Telephone Number*", placeholder="Enter phone number...").props("type=tel outlined maxlength=20").classes(input_classes)
                        phone_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
                        def validate_phone(e=None):
                            value = phone_input.value or ''
                            if not value.strip():
                                phone_error.text = "Please enter the telephone number."
                                phone_error.style('display:block')
                                phone_input.classes('border border-red-600')
                                return False
                            else:
                                phone_error.text = ''
                                phone_error.style('display:none')
                                phone_input.classes(remove='border border-red-600')
                                return True
                        phone_input.on('blur', validate_phone)
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Email").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        email_input = ui.input(label="Email*", placeholder="Enter email...").props("type=email outlined maxlength=60").classes(input_classes)
                        email_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
                        def validate_email(e=None):
                            value = email_input.value or ''
                            if not value.strip():
                                email_error.text = "Please enter the email."
                                email_error.style('display:block')
                                email_input.classes('border border-red-600')
                                return False
                            elif '@' not in value or '.' not in value:
                                email_error.text = "Please enter a valid email address."
                                email_error.style('display:block')
                                email_input.classes('border border-red-600')
                                return False
                            else:
                                email_error.text = ''
                                email_error.style('display:none')
                                email_input.classes(remove='border border-red-600')
                                return True
                        email_input.on('blur', validate_email)

                # Row 7 - Last Due Diligence Date & Next Required Due Diligence (days)
                with ui.element('div').classes(f"{row_classes} {std_row_height}"):
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Last Due Diligence Date").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        with ui.input('MM/DD/YYYY', value='08/25/2025').classes(input_classes).props("outlined") as due_diligence_date:
                            due_diligence_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
                            with ui.menu().props('no-parent-event') as due_diligence_menu:
                                with ui.date(value='2025-08-25').props('mask=MM/DD/YYYY').bind_value(due_diligence_date, 
                                    forward=lambda d: d.replace('-', '/') if d else '', 
                                    backward=lambda d: d.replace('/', '-') if d else ''):
                                    with ui.row().classes('justify-end'):
                                        ui.button('Close', on_click=due_diligence_menu.close).props('flat')
                            with due_diligence_date.add_slot('append'):
                                ui.icon('edit_calendar').on('click', due_diligence_menu.open).classes('cursor-pointer')
                        def validate_due_diligence(e=None):
                            value = due_diligence_date.value or ''
                            if not value.strip():
                                due_diligence_error.text = "Please enter the last due diligence date."
                                due_diligence_error.style('display:block')
                                due_diligence_date.classes('border border-red-600')
                                return False
                            else:
                                due_diligence_error.text = ''
                                due_diligence_error.style('display:none')
                                due_diligence_date.classes(remove='border border-red-600')
                                return True
                        due_diligence_date.on('blur', validate_due_diligence)
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Next Required Due Diligence").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes + " flex flex-col"):
                        next_due_options = ["15", "30", "60", "90", "120"]
                        next_due_input = ui.select(options=next_due_options, value="30", label="Days*").classes(input_classes).props("outlined")
                        next_due_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
                        def validate_next_due(e=None):
                            value = next_due_input.value or ''
                            if not value.strip() or value not in next_due_options:
                                next_due_error.text = "Please select the next required due diligence days."
                                next_due_error.style('display:block')
                                next_due_input.classes('border border-red-600')
                                return False
                            else:
                                next_due_error.text = ''
                                next_due_error.style('display:none')
                                next_due_input.classes(remove='border border-red-600')
                                return True
                        next_due_input.on('blur', validate_next_due)

                # Row 8 - Next Due Diligence Alert & Frequency (in days)
                with ui.element('div').classes(f"{row_classes} {std_row_height}"):
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Next Required Due Diligence Alert").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        next_alert_input = ui.input(label="Days*", value="15").props("type=number outlined maxlength=4").classes(input_classes)
                        next_alert_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
                        def validate_next_alert(e=None):
                            value = next_alert_input.value or ''
                            if not value.strip() or not value.isdigit():
                                next_alert_error.text = "Please enter the next due diligence alert days."
                                next_alert_error.style('display:block')
                                next_alert_input.classes('border border-red-600')
                                return False
                            else:
                                next_alert_error.text = ''
                                next_alert_error.style('display:none')
                                next_alert_input.classes(remove='border border-red-600')
                                return True
                        next_alert_input.on('blur', validate_next_alert)
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Frequency (in days)").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes + " flex flex-col"):
                        freq_options = ["15", "30", "60", "90", "120"]
                        freq_input = ui.select(options=freq_options, value="90", label="Days*").classes(input_classes).props("outlined")
                        freq_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
                        def validate_freq(e=None):
                            value = freq_input.value or ''
                            if not value.strip() or value not in freq_options:
                                freq_error.text = "Please select the frequency in days."
                                freq_error.style('display:block')
                                freq_input.classes('border border-red-600')
                                return False
                            else:
                                freq_error.text = ''
                                freq_error.style('display:none')
                                freq_input.classes(remove='border border-red-600')
                                return True
                        freq_input.on('blur', validate_freq)

                # Row 9 - Due Diligence Upload & Non-Disclosure Agreement Upload
                with ui.element('div').classes(f"{row_classes} h-30"):
                    # Due Diligence
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Due Diligence").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes + " flex flex-col"):
                        due_diligence_file = {'file': None}
                        due_diligence_name = ui.input(label="Due Diligence Name*", placeholder="Document name...").classes("w-full font-[segoe ui] mt-2").props("outlined maxlength=100")
                        due_diligence_signed_date = ui.input('Signed Date*', value='').classes("w-full font-[segoe ui] mt-2").props("outlined")
                        with ui.menu().props('no-parent-event') as dd_signed_menu:
                            with ui.date().props('mask=YYYY-MM-DD').bind_value(due_diligence_signed_date, forward=lambda d: d, backward=lambda d: d):
                                with ui.row().classes('justify-end'):
                                    ui.button('Close', on_click=dd_signed_menu.close).props('flat')
                        with due_diligence_signed_date.add_slot('append'):
                            ui.icon('edit_calendar').on('click', dd_signed_menu.open).classes('cursor-pointer')
                        def handle_due_diligence_upload(e):
                            if hasattr(e, 'files') and e.files:
                                due_diligence_file['file'] = getattr(e.files[0], 'file', e.files[0])
                                ui.notify(f'Due Diligence document uploaded.', type='positive')
                        ui.upload(on_upload=handle_due_diligence_upload, multiple=True, label="Upload due diligence").props('accept=.pdf color=primary outlined').classes("w-full")

                    # NDA
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Non-Disclosure Agreement").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes + " flex flex-col"):
                        nda_file = {'file': None}
                        nda_name = ui.input(label="NDA Name*", placeholder="Document name...").classes("w-full font-[segoe ui] mt-2").props("outlined maxlength=100")
                        nda_signed_date = ui.input('Signed Date*', value='').classes("w-full font-[segoe ui] mt-2").props("outlined")
                        with ui.menu().props('no-parent-event') as nda_signed_menu:
                            with ui.date().props('mask=YYYY-MM-DD').bind_value(nda_signed_date, forward=lambda d: d, backward=lambda d: d):
                                with ui.row().classes('justify-end'):
                                    ui.button('Close', on_click=nda_signed_menu.close).props('flat')
                        with nda_signed_date.add_slot('append'):
                            ui.icon('edit_calendar').on('click', nda_signed_menu.open).classes('cursor-pointer')
                        def handle_nda_upload(e):
                            if hasattr(e, 'files') and e.files:
                                nda_file['file'] = getattr(e.files[0], 'file', e.files[0])
                                ui.notify(f'NDA document uploaded.', type='positive')
                        ui.upload(on_upload=handle_nda_upload, multiple=True, label="Upload NDA").props('accept=.pdf color=primary outlined').classes("w-full")

                # Row 10 - Integrity Policy Upload & Risk Assessment Form Upload
                with ui.element('div').classes(f"{row_classes} h-30"):
                    # Integrity Policy
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Integrity Policy").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes + " flex flex-col"):
                        integrity_policy_file = {'file': None}
                        integrity_policy_name = ui.input(label="Integrity Policy Name*", placeholder="Document name...").classes("w-full font-[segoe ui] mt-2").props("outlined maxlength=100")
                        integrity_policy_signed_date = ui.input('Signed Date*', value='').classes("w-full font-[segoe ui] mt-2").props("outlined")
                        with ui.menu().props('no-parent-event') as ip_signed_menu:
                            with ui.date().props('mask=YYYY-MM-DD').bind_value(integrity_policy_signed_date, forward=lambda d: d, backward=lambda d: d):
                                with ui.row().classes('justify-end'):
                                    ui.button('Close', on_click=ip_signed_menu.close).props('flat')
                        with integrity_policy_signed_date.add_slot('append'):
                            ui.icon('edit_calendar').on('click', ip_signed_menu.open).classes('cursor-pointer')
                        def handle_integrity_policy_upload(e):
                            if hasattr(e, 'files') and e.files:
                                integrity_policy_file['file'] = getattr(e.files[0], 'file', e.files[0])
                                ui.notify(f'Integrity Policy document uploaded.', type='positive')
                        ui.upload(on_upload=handle_integrity_policy_upload, multiple=True, label="Upload policy").props('accept=.pdf color=primary outlined').classes("w-full")

                    # Risk Assessment
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Risk Assessment Form").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes + " flex flex-col"):
                        risk_assessment_file = {'file': None}
                        risk_assessment_name = ui.input(label="Risk Assessment Name*", placeholder="Document name...").classes("w-full font-[segoe ui] mt-2").props("outlined maxlength=100")
                        risk_assessment_signed_date = ui.input('Signed Date*', value='').classes("w-full font-[segoe ui] mt-2").props("outlined")
                        with ui.menu().props('no-parent-event') as ra_signed_menu:
                            with ui.date().props('mask=YYYY-MM-DD').bind_value(risk_assessment_signed_date, forward=lambda d: d, backward=lambda d: d):
                                with ui.row().classes('justify-end'):
                                    ui.button('Close', on_click=ra_signed_menu.close).props('flat')
                        with risk_assessment_signed_date.add_slot('append'):
                            ui.icon('edit_calendar').on('click', ra_signed_menu.open).classes('cursor-pointer')
                        def handle_risk_assessment_upload(e):
                            if hasattr(e, 'files') and e.files:
                                risk_assessment_file['file'] = getattr(e.files[0], 'file', e.files[0])
                                ui.notify(f'Risk Assessment document uploaded.', type='positive')
                        ui.upload(on_upload=handle_risk_assessment_upload, multiple=True, label="Upload form").props('accept=.pdf color=primary outlined').classes("w-full")
                
                # Row 11 - Attention (standard size row for description)
                with ui.element('div').classes(f"{row_classes} h-24"):
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Attention").classes(label_classes)
                    with ui.element('div').classes(f"{input_cell_classes} mt-4"):
                        attention_input = ui.textarea(label="Attention*").classes("w-full font-[segoe ui] h-20").props("outlined maxlength=200")
                        attention_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
                        def validate_attention(e=None):
                            value = attention_input.value or ''
                            if not value.strip():
                                attention_error.text = "Please enter the attention/description."
                                attention_error.style('display:block')
                                attention_input.classes('border border-red-600')
                                return False
                            else:
                                attention_error.text = ''
                                attention_error.style('display:none')
                                attention_input.classes(remove='border border-red-600')
                                return True
                        attention_input.on('blur', validate_attention)
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        ui.label("").classes(input_classes)
                
                # Row 12 - Submit and Cancel buttons inside the table
                with ui.element('div').classes("flex w-full h-16"):
                    with ui.element('div').classes("bg-[#144c8e] w-[16.6%] flex items-center"):
                        ui.label("").classes("text-white font-[segoe ui] py-2 px-4 h-full flex items-center")
                    with ui.element('div').classes("bg-white p-2 w-[33.3%]"):
                        ui.label("").classes("w-full font-[segoe ui]")
                    with ui.element('div').classes("bg-[#144c8e] w-[16.6%] flex items-center"):
                        ui.label("").classes("text-white font-[segoe ui] py-2 px-4 h-full flex items-center")
                    with ui.element('div').classes("bg-white p-2 w-[33.3%] flex justify-end gap-4"):
                        def clear_form():
                            ab_select.value = "Please select"
                            moa_select.value = "Please select"
                            bank_select.value = "Please select"
                            cif_input.value = ""
                            cif_input.set_visibility(False)
                            vendor_name_input.value = ""
                            contact_person_input.value = ""
                            address1_input.value = ""
                            address2_input.value = ""
                            city_input.value = ""
                            state_input.value = ""
                            zip_input.value = ""
                            country_select.value = "Please select"
                            phone_input.value = ""
                            email_input.value = ""
                            due_diligence_date.value = ""
                            next_due_input.value = "30"
                            next_alert_input.value = "15"
                            freq_input.value = "90"
                            due_diligence_file['file'] = None
                            due_diligence_name.value = ""
                            due_diligence_signed_date.value = ""
                            nda_file['file'] = None
                            nda_name.value = ""
                            nda_signed_date.value = ""
                            integrity_policy_file['file'] = None
                            integrity_policy_name.value = ""
                            integrity_policy_signed_date.value = ""
                            risk_assessment_file['file'] = None
                            risk_assessment_name.value = ""
                            risk_assessment_signed_date.value = ""
                            attention_input.value = ""
                            # Hide all error labels
                            ab_error.text = moa_error.text = bank_error.text = cif_error.text = ""
                            vendor_name_error.text = contact_person_error.text = address1_error.text = address2_error.text = city_error.text = state_error.text = zip_error.text = country_error.text = phone_error.text = email_error.text = due_diligence_error.text = next_due_error.text = next_alert_error.text = freq_error.text = attention_error.text = ""
                            ab_error.style('display:none')
                            moa_error.style('display:none')
                            bank_error.style('display:none')
                            cif_error.style('display:none')
                            vendor_name_error.style('display:none')
                            contact_person_error.style('display:none')
                            address1_error.style('display:none')
                            address2_error.style('display:none')
                            city_error.style('display:none')
                            state_error.style('display:none')
                            zip_error.style('display:none')
                            country_error.style('display:none')
                            phone_error.style('display:none')
                            email_error.style('display:none')
                            due_diligence_error.style('display:none')
                            next_due_error.style('display:none')
                            next_alert_error.style('display:none')
                            freq_error.style('display:none')
                            attention_error.style('display:none')
                        ui.button("Cancel", icon="close", on_click=clear_form).props("flat").classes("text-gray-700")
                        def submit_form():
                            validations = [
                                validate_country(),
                                validate_vendor_name(),
                                validate_contact_person(),
                                validate_ab_customer(),
                                validate_moa(),
                                validate_bank(),
                                validate_address1(),
                                validate_address2(),
                                validate_city(),
                                validate_state(),
                                validate_zip(),
                                validate_phone(),
                                validate_email(),
                                validate_due_diligence(),
                                validate_next_due(),
                                validate_next_alert(),
                                validate_freq(),
                                validate_attention()
                            ]
                            if not all(validations):
                                ui.notify('Please fix all required fields before submitting.', type='negative')
                                return
                            # Collect all field values in backend format
                            vendor_data = {
                                "vendor_name": vendor_name_input.value,
                                "vendor_contact_person": contact_person_input.value,
                                "vendor_country": country_select.value,
                                "material_outsourcing_arrangement": moa_select.value,
                                "bank_customer": bank_select.value,
                                "cif": cif_input.value if bank_select.value in ["Aruba Bank", "Orco Bank"] else "",
                                "addresses": [
                                    {
                                        "address": address1_input.value,
                                        "city": city_input.value,
                                        "state": state_input.value,
                                        "zip_code": zip_input.value
                                    }
                                ],
                                "emails": [
                                    {"email": email_input.value}
                                ],
                                "phones": [
                                    {"area_code": "+1", "phone_number": phone_input.value}
                                ],
                                "due_diligence_required": "No"
                            }
                            url = "http://localhost:8000/api/v1/vendors/"
                            files = {'vendor_data': (None, json.dumps(vendor_data))}
                            # Add files and metadata if present
                            if due_diligence_file['file']:
                                files['due_diligence_doc'] = ('due_diligence.pdf', due_diligence_file['file'], 'application/pdf')
                                files['due_diligence_name'] = (None, due_diligence_name.value)
                                files['due_diligence_signed_date'] = (None, due_diligence_signed_date.value)
                            if nda_file['file']:
                                files['non_disclosure_doc'] = ('nda.pdf', nda_file['file'], 'application/pdf')
                                files['non_disclosure_name'] = (None, nda_name.value)
                                files['non_disclosure_signed_date'] = (None, nda_signed_date.value)
                            if risk_assessment_file['file']:
                                files['risk_assessment_doc'] = ('risk_assessment.pdf', risk_assessment_file['file'], 'application/pdf')
                                files['risk_assessment_name'] = (None, risk_assessment_name.value)
                                files['risk_assessment_signed_date'] = (None, risk_assessment_signed_date.value)
                            if integrity_policy_file['file']:
                                files['integrity_policy_doc'] = ('integrity_policy.pdf', integrity_policy_file['file'], 'application/pdf')
                                files['integrity_policy_name'] = (None, integrity_policy_name.value)
                                files['integrity_policy_signed_date'] = (None, integrity_policy_signed_date.value)
                            try:
                                response = requests.post(url, files=files)
                                if response.status_code == 201:
                                    ui.notify('Vendor submitted successfully!', type='positive')
                                    clear_form()
                                else:
                                    ui.notify(f'Error: {response.text}', type='negative')
                            except Exception as e:
                                ui.notify(f'Connection error: {e}', type='negative')
                        ui.button("Submit", icon="check", on_click=submit_form).classes("bg-[#144c8e] text-white")
            
           