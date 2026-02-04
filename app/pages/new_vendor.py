from nicegui import ui
import httpx
import json
import os
import re
from datetime import datetime as dt
from dateutil.relativedelta import relativedelta

from app.core.config import settings
from app.core.constants import DueDiligenceConstants
from app.utils.geo_data import get_country_list, get_us_states, get_country_list_async, get_calling_codes_list

# Import US states from geo_data utility
US_STATES = get_us_states()


EMAIL_REGEX = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


def new_vendor():
            
    with ui.element("div").classes(
        "flex flex-col items-center justify-center mt-8 w-full "
    ):
        ui.input(label="Vendor search", placeholder="Search for existing vendors...").classes("w-1/2 mt-4 font-[segoe ui]").props("outlined")
        # Removed "New Vendor" button per request
        
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
                
                # Row 1 - AB Customer? & Material Outsourcing Arrangement?
                with ui.element('div').classes(f"{row_classes} {std_row_height}"):
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
                    
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Material Outsourcing Arrangement?").classes(label_classes)
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
                
                # Row 2 - Bank Customer & CIF
                with ui.element('div').classes(f"{row_classes} {std_row_height}"):
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
                    
                    # Due Diligence Required field
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Due Diligence Required").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes + " flex flex-col min-h-[70px]"):
                        dd_required_options = ["Please select", "Yes", "No"]
                        dd_required_select = ui.select(
                            options=dd_required_options,
                            value="Please select",
                            label="Due Diligence Required*"
                        ).classes("w-full font-[segoe ui]").props("outlined use-input")
                        dd_required_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')

                        def validate_dd_required(e=None):
                            value = dd_required_select.value
                            if value == "Please select" or not value:
                                dd_required_error.text = "Please indicate if a Due Diligence is required for this new vendor."
                                dd_required_error.style('display:block')
                                dd_required_select.classes('border border-red-600')
                                return False
                            else:
                                dd_required_error.text = ''
                                dd_required_error.style('display:none')
                                dd_required_select.classes(remove='border border-red-600')
                                return True

                        dd_required_select.on('blur', validate_dd_required)

                # Row 3 - Name & Contact Person
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
                
                # Row 4 - Address 1 & Address 2 (with validation)
                # Address blocks (AC: max 2; Aruba restricts to 1; additional block is optional)
                address2_row = None
                city_state2_row = None
                zip2_row = None
                add_address_button = None

                def _clear_second_address_fields() -> None:
                    """Clear 2nd address block values + errors (if created)."""
                    nonlocal address2_input, address2_error, city2_input, city2_error, state2_input, state2_select, state2_error, zip2_input, zip2_error
                    try:
                        address2_input.value = ""
                        city2_input.value = ""
                        state2_input.value = ""
                        state2_select.value = None
                        zip2_input.value = ""
                    except Exception:
                        pass
                    try:
                        address2_error.text = ""
                        address2_error.style("display:none")
                        city2_error.text = ""
                        city2_error.style("display:none")
                        state2_error.text = ""
                        state2_error.style("display:none")
                        zip2_error.text = ""
                        zip2_error.style("display:none")
                        address2_input.classes(remove="border border-red-600")
                        city2_input.classes(remove="border border-red-600")
                        state2_input.classes(remove="border border-red-600")
                        state2_select.classes(remove="border border-red-600")
                        zip2_input.classes(remove="border border-red-600")
                    except Exception:
                        pass

                def add_second_address() -> None:
                    """Show the second address block (max 2 addresses)."""
                    nonlocal address2_row, city_state2_row, zip2_row, add_address_button
                    if address2_row:
                        address2_row.set_visibility(True)
                    if city_state2_row:
                        city_state2_row.set_visibility(True)
                    if zip2_row:
                        zip2_row.set_visibility(True)
                    if add_address_button:
                        add_address_button.set_visibility(False)

                def remove_second_address() -> None:
                    """Hide and clear the second address block."""
                    nonlocal address2_row, city_state2_row, zip2_row, add_address_button
                    _clear_second_address_fields()
                    if address2_row:
                        address2_row.set_visibility(False)
                    if city_state2_row:
                        city_state2_row.set_visibility(False)
                    if zip2_row:
                        zip2_row.set_visibility(False)
                    # Only show Add Address when not Aruba
                    if add_address_button:
                        add_address_button.set_visibility((country_select.value or "") != "Aruba")

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
                        ui.label("Additional Address").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes + " flex flex-col"):
                        # Shown only when Country != Aruba and no 2nd block yet
                        add_address_button = ui.button(
                            "Add Address",
                            icon="add",
                            on_click=add_second_address,
                        ).props("outline color=primary").classes("font-[segoe ui] w-full")

                # Row 5 - City & State (with validation)
                with ui.element('div').classes(f"{row_classes} {std_row_height}") as city_state_row:
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("City").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes + " flex flex-col"):
                        city_input = ui.input(label="City", placeholder="Enter city...").classes(input_classes).props("outlined maxlength=20")
                        city_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
                        def validate_city(e=None):
                            value = city_input.value or ''
                            # City is optional for all countries per AC; only validate basic length when provided
                            if not value.strip():
                                city_error.text = ''
                                city_error.style('display:none')
                                city_input.classes(remove='border border-red-600')
                                return True
                            if len(value.strip()) > 20:
                                city_error.text = "City must be at most 20 characters."
                                city_error.style('display:block')
                                city_input.classes('border border-red-600')
                                return False
                            city_error.text = ''
                            city_error.style('display:none')
                            city_input.classes(remove='border border-red-600')
                            return True
                        city_input.on('blur', validate_city)
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("State").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes + " flex flex-col") as state_container:
                        # Free-text state input (for non-US countries)
                        state_input = ui.input(label="State", placeholder="Enter state...").classes(input_classes).props("outlined maxlength=30")
                        # US states dropdown (shown only when country == United States)
                        state_select = ui.select(options=US_STATES, label="State").classes(input_classes).props("outlined use-input")
                        state_select.set_visibility(False)
                        state_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')

                        def get_state_value():
                            # Helper to get current state value, depending on which control is visible
                            if state_select.visible:
                                return state_select.value or ''
                            return state_input.value or ''

                        def validate_state(e=None):
                            """State is optional for all countries (including United States) per AC."""
                            _ = get_state_value().strip()
                            state_error.text = ''
                            state_error.style('display:none')
                            state_input.classes(remove='border border-red-600')
                            state_select.classes(remove='border border-red-600')
                            return True

                        state_input.on('blur', validate_state)
                        state_select.on('blur', validate_state)

                # Row 6 - Zip Code & Country (with validation)
                with ui.element('div').classes(f"{row_classes} {std_row_height}") as zip_country_row:
                    with ui.element('div').classes(label_cell_classes) as zip_label_cell:
                        zip_label_text = ui.label("Zip Code").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes) as zip_input_cell:
                        zip_input = ui.input(label="Zip Code", placeholder="Enter zip code...").classes(input_classes).props("outlined maxlength=10")
                        zip_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
                        def validate_zip(e=None):
                            value = zip_input.value or ''
                            # Zip is optional; only enforce max length when provided
                            if not value.strip():
                                zip_error.text = ''
                                zip_error.style('display:none')
                                zip_input.classes(remove='border border-red-600')
                                return True
                            if len(value.strip()) > 10:
                                zip_error.text = "Zip Code must be at most 10 characters."
                                zip_error.style('display:block')
                                zip_input.classes('border border-red-600')
                                return False
                            zip_error.text = ''
                            zip_error.style('display:none')
                            zip_input.classes(remove='border border-red-600')
                            return True
                        zip_input.on('blur', validate_zip)
                    with ui.element('div').classes(label_cell_classes) as country_label_cell:
                        ui.label("Country").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes) as country_input_cell:
                        country_options = get_country_list()
                        country_error = ui.label('').classes('text-red-600 text-sm mb-2').style('display:none')
                        # Use placeholder instead of a real "Please select" value,
                        # so the text disappears as soon as the user starts typing.
                        country_select = ui.select(
                            options=country_options,
                            value=None,
                            label="Vendor Country*"
                        ).classes("w-full font-[segoe ui]").props(
                            # use-input: allows typing to filter
                            # clearable: shows an 'x' to clear selection
                            # placeholder: shows 'Please select' when empty
                            'outlined use-input clearable input-debounce=0 placeholder="Please select"'
                        )

                        def validate_country(e=None):
                            value = country_select.value
                            if not value:
                                country_error.text = "Please select the vendor country."
                                country_error.style('display:block')
                                country_select.classes('border border-red-600')
                                return False
                            else:
                                country_error.text = ''
                                country_error.style('display:none')
                                country_select.classes(remove='border border-red-600')
                                return True

                        def on_country_change(e=None):
                            """
                            Adapt address behavior based on selected country (ACs):
                            - Aruba: only Address 1 (mandatory), city/state/zip hidden, no additional address.
                            - Non-Aruba: Address 1 mandatory, optional additional address (max 2),
                              City/State/Zip visible and optional.
                            - United States: State uses dropdown with US states.
                            """
                            country = country_select.value or ''

                            is_aruba = country == "Aruba"
                            is_us = country == "United States"

                            # Update placeholder: only show when no country is selected
                            if country:
                                country_select.props(
                                    'outlined use-input clearable input-debounce=0 placeholder=""'
                                )
                            else:
                                country_select.props(
                                    'outlined use-input clearable input-debounce=0 placeholder="Please select"'
                                )

                            # Aruba: hide City/State/Zip and any additional address
                            if is_aruba:
                                city_state_row.set_visibility(False)
                                # Hide Zip Code content but keep cell containers visible (preserves blue/white backgrounds)
                                zip_label_text.set_visibility(False)
                                zip_input.set_visibility(False)
                                zip_error.style('display:none')
                                # Keep Country cells at their normal width - no changes

                                # Clear related values and errors
                                city_input.value = ""
                                state_input.value = ""
                                state_select.value = None
                                zip_input.value = ""

                                city_error.style('display:none')
                                state_error.style('display:none')
                                city_input.classes(remove='border border-red-600')
                                state_input.classes(remove='border border-red-600')
                                state_select.classes(remove='border border-red-600')
                                zip_input.classes(remove='border border-red-600')

                                # Aruba: force single address entry
                                if add_address_button:
                                    add_address_button.set_visibility(False)
                                remove_second_address()
                            else:
                                # Non-Aruba: show City/State/Zip for address 1
                                city_state_row.set_visibility(True)
                                # Show Zip Code content normally
                                zip_label_text.set_visibility(True)
                                zip_input.set_visibility(True)
                                # Country cells remain at normal width - no changes needed

                                # Show Add Address only when 2nd block is not visible
                                if add_address_button:
                                    add_address_button.set_visibility(
                                        not (address2_row and address2_row.visible)
                                    )

                                # United States: use state dropdown
                                if is_us:
                                    state_input.set_visibility(False)
                                    state_select.set_visibility(True)
                                else:
                                    state_input.set_visibility(True)
                                    state_select.set_visibility(False)

                                # Apply US/non-US state behavior to 2nd block if visible
                                if address2_row and address2_row.visible:
                                    if is_us:
                                        state2_input.set_visibility(False)
                                        state2_select.set_visibility(True)
                                    else:
                                        state2_input.set_visibility(True)
                                        state2_select.set_visibility(False)

                        country_select.on('blur', validate_country)
                        country_select.on('update:model-value', on_country_change)

                # === Additional Address Block (Address 2) - hidden by default; max 2 addresses ===
                with ui.element('div').classes(f"{row_classes} {std_row_height}") as address2_row:
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Address 2").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes + " flex flex-col"):
                        with ui.row().classes("items-center gap-2 w-full"):
                            address2_input = ui.input(
                                label="Address 2",
                                placeholder="Enter address...",
                            ).classes("flex-1 font-[segoe ui]").props("outlined maxlength=60")
                            ui.button(
                                icon="delete",
                                on_click=remove_second_address,
                            ).props("flat round color=negative").classes("mt-2")
                        address2_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        ui.label("")

                with ui.element('div').classes(f"{row_classes} {std_row_height}") as city_state2_row:
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("City").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes + " flex flex-col"):
                        city2_input = ui.input(label="City", placeholder="Enter city...").classes(input_classes).props("outlined maxlength=20")
                        city2_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')

                        def validate_city2(e=None):
                            value = city2_input.value or ''
                            if not value.strip():
                                city2_error.text = ''
                                city2_error.style('display:none')
                                city2_input.classes(remove='border border-red-600')
                                return True
                            if len(value.strip()) > 20:
                                city2_error.text = "City must be at most 20 characters."
                                city2_error.style('display:block')
                                city2_input.classes('border border-red-600')
                                return False
                            city2_error.text = ''
                            city2_error.style('display:none')
                            city2_input.classes(remove='border border-red-600')
                            return True

                        city2_input.on('blur', validate_city2)

                    with ui.element('div').classes(label_cell_classes):
                        ui.label("State").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes + " flex flex-col"):
                        state2_input = ui.input(label="State", placeholder="Enter state...").classes(input_classes).props("outlined maxlength=30")
                        state2_select = ui.select(options=US_STATES, label="State").classes(input_classes).props("outlined use-input")
                        state2_select.set_visibility(False)
                        state2_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')

                        def validate_state2(e=None):
                            # Optional per AC
                            state2_error.text = ''
                            state2_error.style('display:none')
                            state2_input.classes(remove='border border-red-600')
                            state2_select.classes(remove='border border-red-600')
                            return True

                        state2_input.on('blur', validate_state2)
                        state2_select.on('blur', validate_state2)

                with ui.element('div').classes(f"{row_classes} {std_row_height}") as zip2_row:
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Zip Code").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes + " flex flex-col"):
                        zip2_input = ui.input(label="Zip Code", placeholder="Enter zip code...").classes(input_classes).props("outlined maxlength=10")
                        zip2_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')

                        def validate_zip2(e=None):
                            value = zip2_input.value or ''
                            if not value.strip():
                                zip2_error.text = ''
                                zip2_error.style('display:none')
                                zip2_input.classes(remove='border border-red-600')
                                return True
                            if len(value.strip()) > 10:
                                zip2_error.text = "Zip Code must be at most 10 characters."
                                zip2_error.style('display:block')
                                zip2_input.classes('border border-red-600')
                                return False
                            zip2_error.text = ''
                            zip2_error.style('display:none')
                            zip2_input.classes(remove='border border-red-600')
                            return True

                        zip2_input.on('blur', validate_zip2)

                    with ui.element('div').classes(label_cell_classes):
                        ui.label("").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        ui.label("")

                def validate_address2(e=None):
                    """
                    Additional address block validation (AC):
                    - Optional overall (user may not add it).
                    - If user starts filling it, Address 2 becomes required.
                    - City/State/Zip remain optional (just length constraints).
                    """
                    if not address2_row or not address2_row.visible:
                        return True

                    addr2 = (address2_input.value or '').strip()
                    c2 = (city2_input.value or '').strip()
                    z2 = (zip2_input.value or '').strip()
                    s2 = ''
                    try:
                        s2 = (state2_select.value or '').strip() if state2_select.visible else (state2_input.value or '').strip()
                    except Exception:
                        s2 = (state2_input.value or '').strip()

                    any_value = bool(addr2 or c2 or s2 or z2)
                    if not any_value:
                        # Completely empty -> ignore
                        address2_error.text = ''
                        address2_error.style('display:none')
                        address2_input.classes(remove='border border-red-600')
                        return True

                    if not addr2:
                        address2_error.text = "Please enter Address 2."
                        address2_error.style('display:block')
                        address2_input.classes('border border-red-600')
                        return False

                    # Address present; validate optional fields (length rules)
                    address2_error.text = ''
                    address2_error.style('display:none')
                    address2_input.classes(remove='border border-red-600')
                    return validate_city2() and validate_state2() and validate_zip2()

                # Start hidden until user clicks Add Address
                address2_row.set_visibility(False)
                city_state2_row.set_visibility(False)
                zip2_row.set_visibility(False)
                
                # Row 7 - Vendor Phone Numbers & Email
                with ui.element('div').classes(f"{row_classes} {std_row_height}"):
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Vendor Phone Number").classes(label_classes)
                    
                    # Vendor phone numbers (primary mandatory + optional secondary)
                    with ui.element('div').classes(input_cell_classes + " flex flex-col"):
                        phone_number_inputs = []
                        phone_area_selects = []
                        phone_area_code_errors = []  # Error labels for area codes
                        phone_number_errors = []  # Error labels for phone numbers
                        
                        # Get calling codes for dropdown
                        calling_codes_data = get_calling_codes_list()
                        # Format: display both code and country name, value is the full string
                        calling_codes_options = {f"{item['code']} - {item['country']}": f"{item['code']} - {item['country']}" for item in calling_codes_data}
                        
                        # Primary (mandatory) phone number
                        with ui.row().classes("items-center w-full gap-2"):
                            # Area code dropdown
                            phone_area_code_select = ui.select(
                                options=calling_codes_options,
                                value=None,
                                label="Vendor Phone Area Code*"
                            ).classes("flex-1 " + input_classes).props("outlined use-input")
                            phone_area_code_error = ui.label('').classes(
                                'text-red-600 text-xs mt-1 min-h-[18px]'
                            ).style('display:none')
                            
                            # Phone number input
                            primary_phone_input = ui.input(
                                label="Vendor Phone Number*",
                                placeholder="Enter phone number...",
                            ).props("type=tel outlined maxlength=20").classes("flex-1 " + input_classes)
                            primary_phone_error = ui.label('').classes(
                                'text-red-600 text-xs mt-1 min-h-[18px]'
                            ).style('display:none')
                        
                        phone_number_inputs.append(primary_phone_input)
                        phone_area_selects.append(phone_area_code_select)
                        phone_area_code_errors.append(phone_area_code_error)
                        phone_number_errors.append(primary_phone_error)
                        
                        # Container for additional phone fields
                        additional_phones_container = ui.column().classes("mt-2 w-full")
                        
                        def _extract_area_code(area_code_raw):
                            """Extract area code from dropdown value (format: '+1 - United States' -> '+1')"""
                            if not area_code_raw:
                                return None
                            # Extract code from format "+CODE - Country Name"
                            if ' - ' in area_code_raw:
                                return area_code_raw.split(' - ')[0]
                            # If it's already just a code, return it
                            if area_code_raw.startswith('+'):
                                return area_code_raw.split()[0] if ' ' in area_code_raw else area_code_raw
                            return area_code_raw
                        
                        def validate_phone_area_code(area_code_select, error_label):
                            """Validate area code selection"""
                            value = area_code_select.value
                            if not value:
                                error_label.text = "Please enter the Vendor Phone Area Code."
                                error_label.style('display:block')
                                area_code_select.classes('border border-red-600')
                                return False
                            else:
                                error_label.text = ''
                                error_label.style('display:none')
                                area_code_select.classes(remove='border border-red-600')
                                return True
                        
                        def validate_phone_number(phone_input, error_label):
                            """Validate phone number (numeric, spaces, hyphens allowed)"""
                            value = (phone_input.value or '').strip()
                            if not value:
                                error_label.text = "Please enter the Vendor Phone Number."
                                error_label.style('display:block')
                                phone_input.classes('border border-red-600')
                                return False
                            
                            # Check if value contains only spaces/dashes (invalid)
                            if value.replace(' ', '').replace('-', '') == '':
                                error_label.text = "Please enter the Vendor Phone Number."
                                error_label.style('display:block')
                                phone_input.classes('border border-red-600')
                                return False
                            
                            # Check for valid characters (numeric, spaces, hyphens)
                            cleaned = value.replace(' ', '').replace('-', '')
                            if not cleaned.isdigit():
                                error_label.text = "Phone number can only contain numbers, spaces, and hyphens."
                                error_label.style('display:block')
                                phone_input.classes('border border-red-600')
                                return False
                            
                            error_label.text = ''
                            error_label.style('display:none')
                            phone_input.classes(remove='border border-red-600')
                            return True
                        
                        def validate_primary_phone(e=None):
                            """Validate primary phone (both area code and number)"""
                            area_valid = validate_phone_area_code(phone_area_code_select, phone_area_code_error)
                            number_valid = validate_phone_number(primary_phone_input, primary_phone_error)
                            return area_valid and number_valid
                        
                        phone_area_code_select.on('blur', lambda e: validate_phone_area_code(phone_area_code_select, phone_area_code_error))
                        primary_phone_input.on('blur', lambda e: validate_phone_number(primary_phone_input, primary_phone_error))
                        
                        def add_additional_phone_field(e=None):
                            """Add additional phone number field (max 2 phones total)"""
                            if len(phone_number_inputs) >= 2:
                                return
                            
                            with additional_phones_container:
                                with ui.row().classes("items-center w-full gap-2") as phone_row_container:
                                    # Area code dropdown
                                    extra_area_select = ui.select(
                                        options=calling_codes_options,
                                        value=None,
                                        label="Vendor Phone Area Code*"
                                    ).classes("flex-1 " + input_classes).props("outlined use-input")
                                    extra_area_error = ui.label('').classes(
                                        'text-red-600 text-xs mt-1 min-h-[18px]'
                                    ).style('display:none')
                                    
                                    # Phone number input
                                    extra_phone_input = ui.input(
                                        label="Vendor Phone Number*",
                                        placeholder="Enter phone number...",
                                    ).props("type=tel outlined maxlength=20").classes("flex-1 " + input_classes)
                                    extra_phone_error = ui.label('').classes(
                                        'text-red-600 text-xs mt-1 min-h-[18px]'
                                    ).style('display:none')
                                    
                                    def validate_extra_phone(e=None):
                                        area_valid = validate_phone_area_code(extra_area_select, extra_area_error)
                                        number_valid = validate_phone_number(extra_phone_input, extra_phone_error)
                                        return area_valid and number_valid
                                    
                                    extra_area_select.on('blur', lambda e: validate_phone_area_code(extra_area_select, extra_area_error))
                                    extra_phone_input.on('blur', lambda e: validate_phone_number(extra_phone_input, extra_phone_error))
                                    
                                    def remove_extra_phone():
                                        """Remove additional phone number"""
                                        if extra_phone_input in phone_number_inputs:
                                            idx = phone_number_inputs.index(extra_phone_input)
                                            phone_number_inputs.pop(idx)
                                            phone_area_selects.pop(idx)
                                            phone_area_code_errors.pop(idx)
                                            phone_number_errors.pop(idx)
                                        phone_row_container.delete()
                                        # Show Add button again if below max
                                        if len(phone_number_inputs) < 2:
                                            add_phone_button.set_visibility(True)
                                    
                                    ui.button(
                                        "",
                                        icon="delete",
                                        on_click=remove_extra_phone,
                                    ).props("flat round color=negative")
                                    
                                    phone_number_inputs.append(extra_phone_input)
                                    phone_area_selects.append(extra_area_select)
                                    phone_area_code_errors.append(extra_area_error)
                                    phone_number_errors.append(extra_phone_error)
                            
                            # Hide Add button if max reached
                            if len(phone_number_inputs) >= 2:
                                add_phone_button.set_visibility(False)
                        
                        # Add Phone button (max 2 phones total => 1 additional)
                        add_phone_button = ui.button(
                            "Add another phone number",
                            icon="add",
                            on_click=add_additional_phone_field,
                        ).props("outline color=primary").classes("font-[segoe ui] mt-2")
                        
                        def validate_all_vendor_phones(e=None):
                            """Validate all phone numbers"""
                            all_valid = True
                            for i in range(len(phone_number_inputs)):
                                area_valid = validate_phone_area_code(phone_area_selects[i], phone_area_code_errors[i])
                                number_valid = validate_phone_number(phone_number_inputs[i], phone_number_errors[i])
                                if not (area_valid and number_valid):
                                    all_valid = False
                            return all_valid

                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Vendor Email Address").classes(label_classes)

                    # Vendor email addresses (primary + optional secondary)
                    with ui.element('div').classes(input_cell_classes + " flex flex-col") as email_container:
                        email_inputs = []
                        email_error_labels = []

                        # Primary (mandatory) email
                        primary_email_input = ui.input(
                            label="Vendor Email Address*",
                            placeholder="Enter email...",
                        ).props("type=email outlined maxlength=60").classes(input_classes)
                        primary_email_error = ui.label('').classes(
                            'text-red-600 text-xs mt-1 min-h-[18px]'
                        ).style('display:none')

                        email_inputs.append(primary_email_input)
                        email_error_labels.append(primary_email_error)

                        # Container for additional email fields
                        additional_emails_container = ui.column().classes("mt-2 w-full")

                        def add_additional_email_field(e=None):
                            # Allow only one additional email (total max 2)
                            if len(email_inputs) >= 2:
                                return

                            with additional_emails_container:
                                with ui.row().classes("items-center w-full gap-2") as row_container:
                                    extra_input = ui.input(
                                        label="Additional Email",
                                        placeholder="Enter additional email...",
                                    ).props("type=email outlined maxlength=60").classes(
                                        "flex-1 " + input_classes
                                    )
                                    extra_error = ui.label('').classes(
                                        'text-red-600 text-xs min-h-[18px]'
                                    ).style('display:none')

                                    def validate_extra(e=None, _input=extra_input, _error=extra_error):
                                        return validate_email_value(
                                            _input.value,
                                            required=False,
                                            error_label=_error,
                                            input_control=_input,
                                        )

                                    extra_input.on('blur', validate_extra)

                                    def remove_extra():
                                        # Keep primary field always
                                        if extra_input in email_inputs:
                                            idx = email_inputs.index(extra_input)
                                            email_inputs.pop(idx)
                                            email_error_labels.pop(idx)
                                        row_container.delete()
                                        # Show Add button again if below max
                                        if len(email_inputs) < 2:
                                            add_email_button.set_visibility(True)

                                    ui.button(
                                        "",
                                        icon="delete",
                                        on_click=remove_extra,
                                    ).props("flat round color=negative")

                                    email_inputs.append(extra_input)
                                    email_error_labels.append(extra_error)

                            # Hide Add button if max reached
                            if len(email_inputs) >= 2:
                                add_email_button.set_visibility(False)

                        # Add Email button (max 2 emails total => 1 additional)
                        # Style aligned with 'Add Address' button
                        add_email_button = ui.button(
                            "Add Email",
                            icon="add",
                            on_click=add_additional_email_field,
                        ).props("outline color=primary").classes("font-[segoe ui]")

                        def validate_email_value(value: str, required: bool, error_label, input_control):
                            value = (value or '').strip()
                            if not value:
                                if required:
                                    error_label.text = "Please enter the Vendor Email Address."
                                    error_label.style('display:block')
                                    input_control.classes('border border-red-600')
                                    return False
                                # Optional and empty is fine
                                error_label.text = ''
                                error_label.style('display:none')
                                input_control.classes(remove='border border-red-600')
                                return True

                            if not EMAIL_REGEX.match(value):
                                error_label.text = "Please enter a valid email address."
                                error_label.style('display:block')
                                input_control.classes('border border-red-600')
                                return False

                            error_label.text = ''
                            error_label.style('display:none')
                            input_control.classes(remove='border border-red-600')
                            return True

                        def validate_primary_email(e=None):
                            return validate_email_value(
                                primary_email_input.value,
                                required=True,
                                error_label=primary_email_error,
                                input_control=primary_email_input,
                            )

                        primary_email_input.on('blur', validate_primary_email)

                        def validate_all_vendor_emails(e=None):
                            # Validate primary and any additional emails
                            all_valid = True
                            for idx, input_control in enumerate(email_inputs):
                                error_label = email_error_labels[idx]
                                required = idx == 0
                                if not validate_email_value(
                                    input_control.value,
                                    required=required,
                                    error_label=error_label,
                                    input_control=input_control,
                                ):
                                    all_valid = False
                            return all_valid

                # Due Diligence date/alert section - visible only when Due Diligence Required = YES (AC 1)
                last_dd_section = ui.element('div').classes("w-full")
                last_dd_section.set_visibility(False)

                def toggle_last_dd_section():
                    val = (dd_required_select.value or "").strip()
                    last_dd_section.set_visibility(val.lower() == "yes")

                def _dd_display_date(iso_str):
                    """YYYY-MM-DD -> MM/DD/YY for display."""
                    if not iso_str or len(iso_str) < 10:
                        return iso_str or ''
                    return f"{iso_str[5:7]}/{iso_str[8:10]}/{iso_str[2:4]}"

                def _dd_parse_date(mm_dd_yy):
                    """MM/DD/YY -> YYYY-MM-DD for date picker."""
                    if not mm_dd_yy or not (str(mm_dd_yy).strip() if mm_dd_yy else ''):
                        return ''
                    s = str(mm_dd_yy).strip().replace('-', '/')
                    parts = s.split('/')
                    if len(parts) != 3:
                        return ''
                    try:
                        mm, dd, yy = int(parts[0]), int(parts[1]), int(parts[2])
                        year = (2000 + yy) if yy < 100 else yy
                        if not (1 <= mm <= 12 and 1 <= dd <= 31):
                            return ''
                        return f"{year:04d}-{mm:02d}-{dd:02d}"
                    except (ValueError, TypeError):
                        return ''

                def _compute_next_required_dd_date(last_dd_str, moa_value):
                    """Last DD (MM/DD/YY or YYYY-MM-DD) + 3 years if MOA=Yes else +5 years. Returns MM/DD/YY or ''."""
                    if not last_dd_str or not str(last_dd_str).strip():
                        return ''
                    s = str(last_dd_str).strip().replace('-', '/')
                    parts = s.split('/')
                    if len(parts) != 3:
                        if len(s) == 10 and s[4] == '/' and s[7] == '/':
                            parts = [s[:4], s[5:7], s[8:10]]
                        else:
                            return ''
                    try:
                        if len(parts[0]) == 4:  # YYYY-MM-DD
                            y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
                        else:
                            mm, dd, yy = int(parts[0]), int(parts[1]), int(parts[2])
                            y = (2000 + yy) if yy < 100 else yy
                            m, d = mm, dd
                        base = dt(y, m, d)
                    except (ValueError, TypeError):
                        return ''
                    years = DueDiligenceConstants.MATERIAL_OUTSOURCING_YEARS if (str(moa_value or "").strip().lower() == "yes") else DueDiligenceConstants.NON_MATERIAL_OUTSOURCING_YEARS
                    next_dt = base + relativedelta(years=years)
                    return f"{next_dt.month:02d}/{next_dt.day:02d}/{next_dt.year % 100:02d}"

                with last_dd_section:
                    # Row 8 - Last Due Diligence Date (MM/DD/YY) & Next Required Due Diligence Date (AC: date, calculated, editable)
                    with ui.element('div').classes(f"{row_classes} {std_row_height}"):
                        with ui.element('div').classes(label_cell_classes):
                            ui.label("Last Due Diligence Date").classes(label_classes)
                        with ui.element('div').classes(input_cell_classes):
                            with ui.input('MM/DD/YY', value='').classes(input_classes).props("outlined") as due_diligence_date:
                                due_diligence_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
                                with ui.menu().props('no-parent-event') as due_diligence_menu:
                                    with ui.date(value=None).props('mask=MM/DD/YY').bind_value(due_diligence_date,
                                        forward=_dd_display_date,
                                        backward=_dd_parse_date):
                                        with ui.row().classes('justify-end'):
                                            ui.button('Close', on_click=due_diligence_menu.close).props('flat')
                                with due_diligence_date.add_slot('append'):
                                    ui.icon('edit_calendar').on('click', due_diligence_menu.open).classes('cursor-pointer')
                            def validate_due_diligence(e=None):
                                value = (due_diligence_date.value or '').strip()
                                if not value:
                                    due_diligence_error.text = "Please enter the Last Due Diligence date."
                                    due_diligence_error.style('display:block')
                                    due_diligence_date.classes('border border-red-600')
                                    return False
                                due_diligence_error.text = ''
                                due_diligence_error.style('display:none')
                                due_diligence_date.classes(remove='border border-red-600')
                                return True
                            due_diligence_date.on('blur', validate_due_diligence)
                        with ui.element('div').classes(label_cell_classes):
                            ui.label("Next Required Due Diligence Date").classes(label_classes)
                        with ui.element('div').classes(input_cell_classes + " flex flex-col"):
                            with ui.input('MM/DD/YY', value='').classes(input_classes).props("outlined") as next_required_dd_date:
                                next_required_dd_date_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
                                with ui.menu().props('no-parent-event') as next_required_dd_menu:
                                    with ui.date(value=None).props('mask=MM/DD/YY').bind_value(next_required_dd_date,
                                        forward=_dd_display_date,
                                        backward=_dd_parse_date):
                                        with ui.row().classes('justify-end'):
                                            ui.button('Close', on_click=next_required_dd_menu.close).props('flat')
                                with next_required_dd_date.add_slot('append'):
                                    ui.icon('edit_calendar').on('click', next_required_dd_menu.open).classes('cursor-pointer')
                            def validate_next_required_dd_date(e=None):
                                value = (next_required_dd_date.value or '').strip()
                                if not value:
                                    next_required_dd_date_error.text = "Please provide the Next Required Due Diligence Date"
                                    next_required_dd_date_error.style('display:block')
                                    next_required_dd_date.classes('border border-red-600')
                                    return False
                                next_required_dd_date_error.text = ''
                                next_required_dd_date_error.style('display:none')
                                next_required_dd_date.classes(remove='border border-red-600')
                                return True
                            next_required_dd_date.on('blur', validate_next_required_dd_date)

                    def update_next_required_dd_date():
                        calculated = _compute_next_required_dd_date(due_diligence_date.value, moa_select.value)
                        if calculated:
                            next_required_dd_date.value = calculated

                    # Row 9 - Next Due Diligence Alert & Frequency (in days)
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
                            ui.label("Next Required Due Diligence Alert Frequency").classes(label_classes)
                        with ui.element('div').classes(input_cell_classes + " flex flex-col"):
                            freq_options = ["15 days", "30 days", "60 days", "90 days", "120 days"]
                            freq_input = ui.select(options=freq_options, value="90 days", label="Next Required Due Diligence Alert Frequency*").classes(input_classes).props("outlined")
                            freq_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
                            def validate_freq(e=None):
                                value = freq_input.value or ''
                                if not value.strip() or value not in freq_options:
                                    freq_error.text = "Please provide the Next Required Due Diligence Alert Frequency"
                                    freq_error.style('display:block')
                                    freq_input.classes('border border-red-600')
                                    return False
                                else:
                                    freq_error.text = ''
                                    freq_error.style('display:none')
                                    freq_input.classes(remove='border border-red-600')
                                    return True
                            freq_input.on('blur', validate_freq)

                due_diligence_date.on_value_change(lambda e: update_next_required_dd_date())
                moa_select.on_value_change(lambda e: update_next_required_dd_date())

                dd_required_select.on_value_change(lambda e: toggle_last_dd_section())
                toggle_last_dd_section()  # set initial visibility from current value

                # Row 10 - Due Diligence Upload & Non-Disclosure Agreement Upload
                with ui.element('div').classes(f"{row_classes} min-h-[200px]"):
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
                        due_diligence_upload_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
                        async def handle_due_diligence_upload(e):
                            if hasattr(e, 'file') and e.file:
                                file_content = await e.file.read()
                                due_diligence_file['file'] = file_content
                                due_diligence_upload_error.text = ''
                                due_diligence_upload_error.style('display:none')
                                ui.notify(f'Due Diligence document uploaded: {e.file.name}', type='positive')
                        due_diligence_upload = ui.upload(on_upload=handle_due_diligence_upload, auto_upload=True, multiple=False, label="Upload due diligence (PDF)").props('accept=.pdf color=primary outlined').classes("w-full mt-2")

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
                        nda_upload_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
                        async def handle_nda_upload(e):
                            if hasattr(e, 'file') and e.file:
                                file_content = await e.file.read()
                                nda_file['file'] = file_content
                                nda_upload_error.text = ''
                                nda_upload_error.style('display:none')
                                ui.notify(f'NDA document uploaded: {e.file.name}', type='positive')
                        nda_upload = ui.upload(on_upload=handle_nda_upload, auto_upload=True, multiple=False, label="Upload NDA (PDF)").props('accept=.pdf color=primary outlined').classes("w-full mt-2")

                # Row 11 - Integrity Policy Upload & Risk Assessment Form Upload
                with ui.element('div').classes(f"{row_classes} min-h-[200px]"):
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
                        async def handle_integrity_policy_upload(e):
                            if hasattr(e, 'file') and e.file:
                                file_content = await e.file.read()
                                integrity_policy_file['file'] = file_content
                                ui.notify(f'Integrity Policy document uploaded: {e.file.name}', type='positive')
                        integrity_policy_upload = ui.upload(on_upload=handle_integrity_policy_upload, auto_upload=True, multiple=False, label="Upload policy (PDF)").props('accept=.pdf color=primary outlined').classes("w-full mt-2")

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
                        risk_assessment_upload_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
                        async def handle_risk_assessment_upload(e):
                            if hasattr(e, 'file') and e.file:
                                file_content = await e.file.read()
                                risk_assessment_file['file'] = file_content
                                risk_assessment_upload_error.text = ''
                                risk_assessment_upload_error.style('display:none')
                                ui.notify(f'Risk Assessment document uploaded: {e.file.name}', type='positive')
                        risk_assessment_upload = ui.upload(on_upload=handle_risk_assessment_upload, auto_upload=True, multiple=False, label="Upload form (PDF)").props('accept=.pdf color=primary outlined').classes("w-full mt-2")

                # Row 11b - Business Continuity Plan & Disaster Recovery Plan (Risk Assessment section, optional)
                with ui.element('div').classes(f"{row_classes} min-h-[200px]"):
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Business Continuity Plan").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes + " flex flex-col"):
                        business_continuity_file = {'file': None}
                        business_continuity_name = ui.input(label="Business Continuity Name", placeholder="Document name...").classes("w-full font-[segoe ui] mt-2").props("outlined maxlength=100")
                        business_continuity_signed_date = ui.input('Signed Date', value='').classes("w-full font-[segoe ui] mt-2").props("outlined")
                        with ui.menu().props('no-parent-event') as bc_signed_menu:
                            with ui.date().props('mask=YYYY-MM-DD').bind_value(business_continuity_signed_date, forward=lambda d: d, backward=lambda d: d):
                                with ui.row().classes('justify-end'):
                                    ui.button('Close', on_click=bc_signed_menu.close).props('flat')
                        with business_continuity_signed_date.add_slot('append'):
                            ui.icon('edit_calendar').on('click', bc_signed_menu.open).classes('cursor-pointer')
                        async def handle_business_continuity_upload(e):
                            if hasattr(e, 'file') and e.file:
                                file_content = await e.file.read()
                                business_continuity_file['file'] = file_content
                                ui.notify(f'Business Continuity Plan document uploaded: {e.file.name}', type='positive')
                        business_continuity_upload = ui.upload(on_upload=handle_business_continuity_upload, auto_upload=True, multiple=False, label="Upload (PDF, optional)").props('accept=.pdf color=primary outlined').classes("w-full mt-2")

                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Disaster Recovery Plan").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes + " flex flex-col"):
                        disaster_recovery_file = {'file': None}
                        disaster_recovery_name = ui.input(label="Disaster Recovery Name", placeholder="Document name...").classes("w-full font-[segoe ui] mt-2").props("outlined maxlength=100")
                        disaster_recovery_signed_date = ui.input('Signed Date', value='').classes("w-full font-[segoe ui] mt-2").props("outlined")
                        with ui.menu().props('no-parent-event') as dr_signed_menu:
                            with ui.date().props('mask=YYYY-MM-DD').bind_value(disaster_recovery_signed_date, forward=lambda d: d, backward=lambda d: d):
                                with ui.row().classes('justify-end'):
                                    ui.button('Close', on_click=dr_signed_menu.close).props('flat')
                        with disaster_recovery_signed_date.add_slot('append'):
                            ui.icon('edit_calendar').on('click', dr_signed_menu.open).classes('cursor-pointer')
                        async def handle_disaster_recovery_upload(e):
                            if hasattr(e, 'file') and e.file:
                                file_content = await e.file.read()
                                disaster_recovery_file['file'] = file_content
                                ui.notify(f'Disaster Recovery Plan document uploaded: {e.file.name}', type='positive')
                        disaster_recovery_upload = ui.upload(on_upload=handle_disaster_recovery_upload, auto_upload=True, multiple=False, label="Upload (PDF, optional)").props('accept=.pdf color=primary outlined').classes("w-full mt-2")

                # Row 11c - Insurance Policy (Risk Assessment section, optional)
                with ui.element('div').classes(f"{row_classes} min-h-[200px]"):
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Insurance Policy").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes + " flex flex-col"):
                        insurance_policy_file = {'file': None}
                        insurance_policy_name = ui.input(label="Insurance Policy Name", placeholder="Document name...").classes("w-full font-[segoe ui] mt-2").props("outlined maxlength=100")
                        insurance_policy_signed_date = ui.input('Signed Date', value='').classes("w-full font-[segoe ui] mt-2").props("outlined")
                        with ui.menu().props('no-parent-event') as ins_signed_menu:
                            with ui.date().props('mask=YYYY-MM-DD').bind_value(insurance_policy_signed_date, forward=lambda d: d, backward=lambda d: d):
                                with ui.row().classes('justify-end'):
                                    ui.button('Close', on_click=ins_signed_menu.close).props('flat')
                        with insurance_policy_signed_date.add_slot('append'):
                            ui.icon('edit_calendar').on('click', ins_signed_menu.open).classes('cursor-pointer')
                        async def handle_insurance_policy_upload(e):
                            if hasattr(e, 'file') and e.file:
                                file_content = await e.file.read()
                                insurance_policy_file['file'] = file_content
                                ui.notify(f'Insurance Policy document uploaded: {e.file.name}', type='positive')
                        insurance_policy_upload = ui.upload(on_upload=handle_insurance_policy_upload, auto_upload=True, multiple=False, label="Upload (PDF, optional)").props('accept=.pdf color=primary outlined').classes("w-full mt-2")
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        ui.label("").classes(input_classes)
                
                # Row 12 - Attention (standard size row for description)
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
                
                # Row 13 - Submit and Cancel buttons inside the table
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
                            city_input.value = ""
                            state_input.value = ""
                            state_select.value = None
                            zip_input.value = ""
                            country_select.value = None
                            
                            # Clear phone fields
                            def clear_additional_phones():
                                """Clear and remove additional phone number fields"""
                                if len(phone_number_inputs) > 1:
                                    # Remove additional phones (keep primary)
                                    while len(phone_number_inputs) > 1:
                                        phone_number_inputs.pop()
                                        phone_area_selects.pop()
                                        phone_area_code_errors.pop()
                                        phone_number_errors.pop()
                                    # Clear container
                                    additional_phones_container.clear()
                                    # Show Add button
                                    add_phone_button.set_visibility(True)
                            
                            # Clear primary phone
                            phone_area_code_select.value = None
                            primary_phone_input.value = ""
                            phone_area_code_error.text = ''
                            phone_area_code_error.style('display:none')
                            primary_phone_error.text = ''
                            primary_phone_error.style('display:none')
                            phone_area_code_select.classes(remove='border border-red-600')
                            primary_phone_input.classes(remove='border border-red-600')
                            
                            # Clear additional phones
                            clear_additional_phones()
                            
                            # Clear + hide optional additional address block
                            remove_second_address()
                            # Reset vendor email fields
                            for inp in email_inputs:
                                inp.value = ""
                            due_diligence_date.value = ""
                            next_required_dd_date.value = ""
                            next_alert_input.value = "15"
                            freq_input.value = "90 days"
                            
                            # Reset file data
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
                            business_continuity_file['file'] = None
                            business_continuity_name.value = ""
                            business_continuity_signed_date.value = ""
                            disaster_recovery_file['file'] = None
                            disaster_recovery_name.value = ""
                            disaster_recovery_signed_date.value = ""
                            insurance_policy_file['file'] = None
                            insurance_policy_name.value = ""
                            insurance_policy_signed_date.value = ""
                            attention_input.value = ""
                            
                            # Reset upload components UI
                            due_diligence_upload.reset()
                            nda_upload.reset()
                            integrity_policy_upload.reset()
                            risk_assessment_upload.reset()
                            business_continuity_upload.reset()
                            disaster_recovery_upload.reset()
                            insurance_policy_upload.reset()
                            
                            # Hide all error labels
                            ab_error.text = moa_error.text = bank_error.text = cif_error.text = ""
                            vendor_name_error.text = contact_person_error.text = address1_error.text = address2_error.text = city_error.text = state_error.text = zip_error.text = country_error.text = phone_area_code_error.text = primary_phone_error.text = due_diligence_error.text = next_required_dd_date_error.text = next_alert_error.text = freq_error.text = attention_error.text = ""
                            due_diligence_upload_error.text = nda_upload_error.text = risk_assessment_upload_error.text = ""
                            due_diligence_upload_error.style('display:none')
                            nda_upload_error.style('display:none')
                            risk_assessment_upload_error.style('display:none')
                            # Additional address block error labels
                            city2_error.text = state2_error.text = zip2_error.text = ""
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
                            phone_area_code_error.style('display:none')
                            primary_phone_error.style('display:none')
                            primary_email_error.style('display:none')
                            due_diligence_error.style('display:none')
                            next_required_dd_date_error.style('display:none')
                            next_alert_error.style('display:none')
                            freq_error.style('display:none')
                            attention_error.style('display:none')
                            city2_error.style('display:none')
                            state2_error.style('display:none')
                            zip2_error.style('display:none')
                            
                            ui.notify('✨ Vendor form cleared', type='info')
                        ui.button("Cancel", icon="close", on_click=clear_form).props("flat").classes("text-gray-700")
                        async def submit_form():
                            validations = [
                                validate_country(),
                                validate_vendor_name(),
                                validate_contact_person(),
                                validate_ab_customer(),
                                validate_moa(),
                                validate_bank(),
                                validate_dd_required(),
                                validate_address1(),
                                validate_address2(),
                                validate_city(),
                                validate_state(),
                                validate_zip(),
                                validate_all_vendor_phones(),
                                validate_all_vendor_emails(),
                                validate_attention()
                            ]
                            # AC: Last Due Diligence Date mandatory only when visible (Due Diligence Required = YES)
                            if (dd_required_select.value or "").strip().lower() == "yes":
                                validations.extend([
                                    validate_due_diligence(),
                                    validate_next_required_dd_date(),
                                    validate_next_alert(),
                                    validate_freq(),
                                ])
                            if not all(validations):
                                ui.notify('Please fix all required fields before submitting.', type='negative')
                                return
                            # AC 4: Prevent submit if mandatory documents are missing; show message at specific field
                            due_diligence_upload_error.text = ''
                            due_diligence_upload_error.style('display:none')
                            nda_upload_error.text = ''
                            nda_upload_error.style('display:none')
                            risk_assessment_upload_error.text = ''
                            risk_assessment_upload_error.style('display:none')
                            doc_required_msg = "Please upload this required document"
                            if (dd_required_select.value or "").strip().lower() == "yes":
                                if not due_diligence_file.get('file'):
                                    due_diligence_upload_error.text = doc_required_msg
                                    due_diligence_upload_error.style('display:block')
                                    ui.notify(doc_required_msg + ": Due Diligence", type='negative')
                                    return
                                if not nda_file.get('file'):
                                    nda_upload_error.text = doc_required_msg
                                    nda_upload_error.style('display:block')
                                    ui.notify(doc_required_msg + ": Non-Disclosure Agreement", type='negative')
                                    return
                                if (moa_select.value or "").strip().lower() == "yes" and not risk_assessment_file.get('file'):
                                    risk_assessment_upload_error.text = doc_required_msg
                                    risk_assessment_upload_error.style('display:block')
                                    ui.notify(doc_required_msg + ": Risk Assessment Form", type='negative')
                                    return
                            # Determine if due diligence is required based on uploaded files
                            has_due_diligence_docs = bool(due_diligence_file.get('file') or nda_file.get('file'))

                            def parse_mm_dd_yy_to_iso(date_str):
                                """Parse MM/DD/YY to YYYY-MM-DD for API. AC 3: date format MM/DD/YY."""
                                if not date_str or not date_str.strip():
                                    return None
                                s = date_str.strip().replace('-', '/')
                                parts = s.split('/')
                                if len(parts) != 3:
                                    return None
                                try:
                                    mm, dd, yy = int(parts[0]), int(parts[1]), int(parts[2])
                                    year = (2000 + yy) if yy < 100 else yy
                                    if not (1 <= mm <= 12 and 1 <= dd <= 31):
                                        return None
                                    return f"{year:04d}-{mm:02d}-{dd:02d}"
                                except (ValueError, TypeError):
                                    return None

                            def validate_date_format(date_str):
                                """Accept MM/DD/YY (or YYYY-MM-DD) and return YYYY-MM-DD for API."""
                                if not date_str or not date_str.strip():
                                    return None
                                date_str = date_str.strip()
                                if len(date_str) == 10 and date_str[4] == '-' and date_str[7] == '-':
                                    return date_str
                                return parse_mm_dd_yy_to_iso(date_str)
                            
                            # Collect all field values in backend format
                            # Build addresses according to ACs:
                            # - Address 1 always included and mandatory.
                            # - Address 2 included only if user provided a value.
                            # - City/State/Zip optional and omitted when country is Aruba.
                            country_val = country_select.value

                            addresses_payload = []
                            # First address (mandatory)
                            addr1 = {
                                "address": address1_input.value,
                                "city": None,
                                "state": None,
                                "zip_code": None,
                            }
                            if country_val != "Aruba":
                                addr1["city"] = city_input.value or None
                                # Pick the appropriate state source
                                state_val = state_select.value if (country_val == "United States" and state_select.visible) else state_input.value
                                addr1["state"] = state_val or None
                                addr1["zip_code"] = zip_input.value or None
                            addresses_payload.append(addr1)

                            # Second address (optional)
                            if (address2_input.value and address2_input.value.strip()):
                                addr2 = {
                                    "address": address2_input.value,
                                    "city": None,
                                    "state": None,
                                    "zip_code": None,
                                }
                                if country_val != "Aruba":
                                    addr2["city"] = city2_input.value or None
                                    state_val2 = state2_select.value if (country_val == "United States" and state2_select.visible) else state2_input.value
                                    addr2["state"] = state_val2 or None
                                    addr2["zip_code"] = zip2_input.value or None
                                addresses_payload.append(addr2)

                            # Build emails payload (primary + optional additional)
                            emails_payload = []
                            # Primary email is mandatory and already validated
                            if primary_email_input.value and primary_email_input.value.strip():
                                emails_payload.append({"email": primary_email_input.value.strip()})
                            # Optional additional emails
                            for extra_input in email_inputs[1:]:
                                if extra_input.value and extra_input.value.strip():
                                    emails_payload.append({"email": extra_input.value.strip()})

                            # Build phones payload (mandatory primary + optional secondary)
                            phones_payload = []
                            for i in range(len(phone_number_inputs)):
                                area_code_raw = phone_area_selects[i].value
                                area_code = _extract_area_code(area_code_raw)
                                phone_number_val = (phone_number_inputs[i].value or "").strip()
                                phones_payload.append(
                                    {"area_code": area_code, "phone_number": phone_number_val}
                                )

                            vendor_data = {
                                "vendor_name": vendor_name_input.value,
                                "vendor_contact_person": contact_person_input.value,
                                "vendor_country": country_val,
                                "material_outsourcing_arrangement": moa_select.value,
                                "bank_customer": bank_select.value,
                                "addresses": addresses_payload,
                                "emails": emails_payload,
                                "phones": phones_payload,
                                "due_diligence_required": dd_required_select.value
                            }
                            
                            # Only add CIF if bank customer is Aruba Bank or Orco Bank
                            if bank_select.value in ["Aruba Bank", "Orco Bank"]:
                                vendor_data["cif"] = cif_input.value
                            
                            # Add due diligence fields only when Due Diligence Required = YES (AC 1 & 4)
                            if (dd_required_select.value or "").strip().lower() == "yes":
                                last_dd_date = validate_date_format(due_diligence_date.value)
                                if not last_dd_date:
                                    ui.notify('Please enter a valid Last Due Diligence Date (format: MM/DD/YY)', type='negative')
                                    return
                                next_dd_date_iso = validate_date_format(next_required_dd_date.value)
                                if not next_dd_date_iso:
                                    ui.notify('Please provide the Next Required Due Diligence Date (format: MM/DD/YY)', type='negative')
                                    return
                                vendor_data["last_due_diligence_date"] = last_dd_date
                                vendor_data["next_required_due_diligence_date"] = next_dd_date_iso
                                vendor_data["next_required_due_diligence_alert_frequency"] = freq_input.value
                            # Use environment variable or default to 127.0.0.1 (more reliable than localhost in Docker)
                            api_host = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
                            url = f"{api_host}{settings.api_v1_prefix}/vendors/"
                            
                            # Build files dict - only include vendor_data as form field
                            files = {'vendor_data': (None, json.dumps(vendor_data))}
                            
                            # Debug: Check what files we have
                            print(f"\n📄 Files status:")
                            print(f"  Due Diligence: {'✓' if due_diligence_file.get('file') else '✗'}")
                            print(f"  NDA: {'✓' if nda_file.get('file') else '✗'}")
                            print(f"  Risk Assessment: {'✓' if risk_assessment_file.get('file') else '✗'}")
                            print(f"  Integrity Policy: {'✓' if integrity_policy_file.get('file') else '✗'}")
                            print()
                            
                            # Add files and metadata ONLY if they exist and have content
                            if due_diligence_file.get('file'):
                                dd_name = due_diligence_name.value.strip() if due_diligence_name.value else ''
                                dd_date = due_diligence_signed_date.value.strip() if due_diligence_signed_date.value else ''
                                
                                print(f"📋 Due Diligence fields:")
                                print(f"  Name: '{dd_name}'")
                                print(f"  Date: '{dd_date}'")
                                
                                if not dd_name or not dd_date:
                                    ui.notify('⚠️ Please provide document name and signed date for Due Diligence', type='warning')
                                    return
                                
                                # Validate date format (should be YYYY-MM-DD)
                                if not validate_date_format(dd_date):
                                    ui.notify(f'Invalid date format for Due Diligence signed date: {dd_date}. Expected YYYY-MM-DD', type='negative')
                                    return
                                
                                print(f"Due Diligence doc - Name: {dd_name}, Date: {dd_date}")
                                files['due_diligence_doc'] = ('due_diligence.pdf', due_diligence_file['file'], 'application/pdf')
                                files['due_diligence_name'] = (None, dd_name)
                                files['due_diligence_signed_date'] = (None, dd_date)
                            
                            if nda_file.get('file'):
                                nda_name_val = nda_name.value.strip() if nda_name.value else ''
                                nda_date_val = nda_signed_date.value.strip() if nda_signed_date.value else ''
                                
                                print(f"📋 NDA fields:")
                                print(f"  Name: '{nda_name_val}'")
                                print(f"  Date: '{nda_date_val}'")
                                
                                if not nda_name_val or not nda_date_val:
                                    ui.notify('⚠️ Please provide document name and signed date for NDA', type='warning')
                                    return
                                
                                # Validate date format (should be YYYY-MM-DD)
                                if not validate_date_format(nda_date_val):
                                    ui.notify(f'Invalid date format for NDA signed date: {nda_date_val}. Expected YYYY-MM-DD', type='negative')
                                    return
                                
                                print(f"NDA doc - Name: {nda_name_val}, Date: {nda_date_val}")
                                files['non_disclosure_doc'] = ('nda.pdf', nda_file['file'], 'application/pdf')
                                files['non_disclosure_name'] = (None, nda_name_val)
                                files['non_disclosure_signed_date'] = (None, nda_date_val)
                            
                            if risk_assessment_file.get('file'):
                                ra_name_val = risk_assessment_name.value.strip() if risk_assessment_name.value else ''
                                ra_date_val = risk_assessment_signed_date.value.strip() if risk_assessment_signed_date.value else ''
                                
                                print(f"📋 Risk Assessment fields:")
                                print(f"  Name: '{ra_name_val}'")
                                print(f"  Date: '{ra_date_val}'")
                                
                                if not ra_name_val or not ra_date_val:
                                    ui.notify('⚠️ Please provide document name and signed date for Risk Assessment', type='warning')
                                    return
                                
                                # Validate date format (should be YYYY-MM-DD)
                                if not validate_date_format(ra_date_val):
                                    ui.notify(f'Invalid date format for Risk Assessment signed date: {ra_date_val}. Expected YYYY-MM-DD', type='negative')
                                    return
                                
                                print(f"Risk Assessment doc - Name: {ra_name_val}, Date: {ra_date_val}")
                                files['risk_assessment_doc'] = ('risk_assessment.pdf', risk_assessment_file['file'], 'application/pdf')
                                files['risk_assessment_name'] = (None, ra_name_val)
                                files['risk_assessment_signed_date'] = (None, ra_date_val)
                            
                            if integrity_policy_file.get('file'):
                                ip_name_val = integrity_policy_name.value.strip() if integrity_policy_name.value else ''
                                ip_date_val = integrity_policy_signed_date.value.strip() if integrity_policy_signed_date.value else ''
                                
                                print(f"📋 Integrity Policy fields:")
                                print(f"  Name: '{ip_name_val}'")
                                print(f"  Date: '{ip_date_val}'")
                                
                                if not ip_name_val or not ip_date_val:
                                    ui.notify('⚠️ Please provide document name and signed date for Integrity Policy', type='warning')
                                    return
                                
                                # Validate date format (should be YYYY-MM-DD)
                                if not validate_date_format(ip_date_val):
                                    ui.notify(f'Invalid date format for Integrity Policy signed date: {ip_date_val}. Expected YYYY-MM-DD', type='negative')
                                    return
                                
                                print(f"Integrity Policy doc - Name: {ip_name_val}, Date: {ip_date_val}")
                                files['integrity_policy_doc'] = ('integrity_policy.pdf', integrity_policy_file['file'], 'application/pdf')
                                files['integrity_policy_name'] = (None, ip_name_val)
                                files['integrity_policy_signed_date'] = (None, ip_date_val)
                            
                            if business_continuity_file.get('file'):
                                bc_name_val = business_continuity_name.value.strip() if business_continuity_name.value else ''
                                bc_date_val = business_continuity_signed_date.value.strip() if business_continuity_signed_date.value else ''
                                if not bc_name_val or not bc_date_val:
                                    ui.notify('Please provide document name and signed date for Business Continuity Plan', type='negative')
                                    return
                                if not validate_date_format(bc_date_val):
                                    ui.notify(f'Invalid date format for Business Continuity signed date. Expected YYYY-MM-DD', type='negative')
                                    return
                                files['business_continuity_doc'] = ('business_continuity.pdf', business_continuity_file['file'], 'application/pdf')
                                files['business_continuity_name'] = (None, bc_name_val)
                                files['business_continuity_signed_date'] = (None, bc_date_val)
                            
                            if disaster_recovery_file.get('file'):
                                dr_name_val = disaster_recovery_name.value.strip() if disaster_recovery_name.value else ''
                                dr_date_val = disaster_recovery_signed_date.value.strip() if disaster_recovery_signed_date.value else ''
                                if not dr_name_val or not dr_date_val:
                                    ui.notify('Please provide document name and signed date for Disaster Recovery Plan', type='negative')
                                    return
                                if not validate_date_format(dr_date_val):
                                    ui.notify(f'Invalid date format for Disaster Recovery signed date. Expected YYYY-MM-DD', type='negative')
                                    return
                                files['disaster_recovery_doc'] = ('disaster_recovery.pdf', disaster_recovery_file['file'], 'application/pdf')
                                files['disaster_recovery_name'] = (None, dr_name_val)
                                files['disaster_recovery_signed_date'] = (None, dr_date_val)
                            
                            if insurance_policy_file.get('file'):
                                ins_name_val = insurance_policy_name.value.strip() if insurance_policy_name.value else ''
                                ins_date_val = insurance_policy_signed_date.value.strip() if insurance_policy_signed_date.value else ''
                                if not ins_name_val or not ins_date_val:
                                    ui.notify('Please provide document name and signed date for Insurance Policy', type='negative')
                                    return
                                if not validate_date_format(ins_date_val):
                                    ui.notify(f'Invalid date format for Insurance Policy signed date. Expected YYYY-MM-DD', type='negative')
                                    return
                                files['insurance_policy_doc'] = ('insurance_policy.pdf', insurance_policy_file['file'], 'application/pdf')
                                files['insurance_policy_name'] = (None, ins_name_val)
                                files['insurance_policy_signed_date'] = (None, ins_date_val)
                            
                            try:
                                # Debug: Log the data being sent
                                print(f"\n{'='*60}")
                                print(f"SUBMITTING VENDOR TO API")
                                print(f"{'='*60}")
                                print(f"Sending vendor data: {json.dumps(vendor_data, indent=2)}")
                                if has_due_diligence_docs:
                                    print(f"Due diligence date: {vendor_data.get('last_due_diligence_date')}")
                                
                                # Print all form fields being sent
                                print(f"\n📤 Form fields being sent:")
                                for key, value in files.items():
                                    if isinstance(value, tuple):
                                        if value[0] is None:  # Form field
                                            print(f"  {key}: '{value[1]}'")
                                        else:  # File upload
                                            print(f"  {key}: <file: {value[0]}>")
                                    else:
                                        print(f"  {key}: {value}")
                                
                                print(f"\nURL: {url}")
                                print(f"{'='*60}\n")
                                
                                async with httpx.AsyncClient(timeout=30.0) as client:
                                    response = await client.post(url, files=files)
                                    
                                    print(f"\n{'='*60}")
                                    print(f"API RESPONSE")
                                    print(f"{'='*60}")
                                    print(f"Status Code: {response.status_code}")
                                    print(f"Response Body: {response.text[:500]}")  # First 500 chars
                                    print(f"{'='*60}\n")
                                    
                                    if response.status_code == 201:
                                        # SUCCESS!
                                        try:
                                            result = response.json()
                                            vendor_id = result.get('vendor_id', 'N/A')
                                            vendor_name = result.get('vendor_name', vendor_data.get('vendor_name'))
                                            ui.notify(
                                                f'✅ SUCCESS! Vendor "{vendor_name}" (ID: {vendor_id}) created successfully!',
                                                type='positive',
                                                position='top',
                                                close_button=True,
                                                timeout=5000
                                            )
                                            print(f"✅ Vendor created successfully: {vendor_id}")
                                            clear_form()
                                        except Exception as parse_error:
                                            print(f"Parse error (but vendor created): {parse_error}")
                                            ui.notify('✅ Vendor created successfully!', type='positive')
                                            clear_form()
                                    else:
                                        # ERROR
                                        error_text = ""
                                        try:
                                            error_json = response.json()
                                            if 'detail' in error_json:
                                                detail = error_json['detail']
                                                
                                                # Check for duplicate vendor error
                                                if 'duplicate key' in str(detail).lower() and 'vendor_id' in str(detail).lower():
                                                    # Extract vendor ID from error
                                                    import re
                                                    match = re.search(r'\(([A-Z]+\d+)\)', str(detail))
                                                    vendor_id = match.group(1) if match else 'unknown'
                                                    error_text = f"⚠️ Vendor ID {vendor_id} already exists. The previous vendor was created successfully!"
                                                    ui.notify(error_text, type='warning', close_button=True, timeout=8000)
                                                    print(f"ℹ️ {error_text}")
                                                    return  # Exit early for duplicate
                                                
                                                # Check for validation errors
                                                if isinstance(detail, dict) and 'errors' in detail:
                                                    errors = detail['errors']
                                                    error_text = '\n'.join(errors) if isinstance(errors, list) else str(errors)
                                                elif 'validation error' in str(detail).lower():
                                                    # Extract the key error message
                                                    error_lines = str(detail).split('\n')
                                                    error_text = '\n'.join([line for line in error_lines if line.strip() and 'For further information' not in line])
                                                else:
                                                    error_text = str(detail)
                                            else:
                                                error_text = str(error_json)
                                        except:
                                            error_text = response.text[:300]
                                        
                                        print(f"❌ Error creating vendor: {error_text}")
                                        ui.notify(f'❌ Error: {error_text}', type='negative', close_button=True, timeout=15000)
                                        
                            except httpx.TimeoutException:
                                print(f"❌ Request timeout")
                                ui.notify('⏱️ Request timed out. Please try again.', type='negative')
                            except httpx.ConnectError as e:
                                print(f"❌ Connection error: {e}")
                                ui.notify('🔌 Cannot connect to server. Make sure it is running.', type='negative')
                            except Exception as e:
                                print(f"❌ Unexpected error: {type(e).__name__}: {e}")
                                import traceback
                                traceback.print_exc()
                                ui.notify(f'❌ Unexpected error: {str(e)}', type='negative')
                        ui.button("Submit", icon="check", on_click=submit_form).classes("bg-[#144c8e] text-white")
            
           