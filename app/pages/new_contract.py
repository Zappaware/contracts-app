from nicegui import ui, app
import httpx
import re
import uuid
from app.utils.navigation import get_dashboard_url
from app.components.breadcrumb import breadcrumb
import json
import os
from app.core.config import settings
from app.models.contract import (
    DepartmentType,
    ExpirationNoticePeriodType,
    NoticePeriodType,
)


def new_contract():
    ui.add_css("""
        .desc-field-col .q-field__control { height: 200px; }
    """)
    # Form persistence: survives page refresh; cleared only on Cancel
    fd = app.storage.user.setdefault('new_contract_form', {})
    # Breadcrumb navigation
    with ui.row().classes("max-w-7xl mx-auto mt-4"):
        breadcrumb([("Home", get_dashboard_url()), ("New Contract", None)])

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
    
    # Vendor Contract: each upload is one row (name + signed date + bytes)
    vendor_contract_docs = []
    
    with ui.element("div").classes("max-w-7xl mx-auto mt-8 w-full px-4").props(f'id="c213"'):
        with ui.element("div").classes("p-8 bg-white rounded-xl mx-auto grid gap-8 shadow-xl border border-gray-200"):
                ui.label("Contract Details").classes("text-lg font-semibold text-gray-800 mb-4")
                # Use real vendors from database
                with ui.column().classes("gap-6 w-[600px] mx-auto items-center"):
                    _vendor_val = fd.get('vendor_select')
                    if _vendor_val not in vendor_names:
                        _vendor_val = vendor_names[0] if vendor_names else None
                    vendor_select = ui.select(
                        options=vendor_names,
                        value=_vendor_val,
                        label="Vendor*",
                    ).classes("w-full font-[segoe ui]").props("outlined").bind_value(
                        fd, "vendor_select"
                    )
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

                    with ui.element('div').classes('w-full desc-field-col'):
                        desc_input = ui.input(
                            label="Description*",
                            placeholder="Brief purpose (max 100 chars)",
                            value=fd.get("desc_input", ""),
                        ).classes("w-full font-[segoe ui]").props(
                            "outlined maxlength=100"
                        ).bind_value(fd, "desc_input")
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
        
                input_classes = "w-full font-[segoe ui]"
                form_row = "grid grid-cols-1 md:grid-cols-2 gap-8 items-stretch"
                form_field = "flex flex-col gap-1"
                
                ui.label("Contract Terms").classes(
                    "text-lg font-semibold text-gray-800 mb-4 mt-8"
                )
                # Row 1 - Termination notice period & contract end date
                _termination_options = [e.value for e in NoticePeriodType]
                _termination_default = NoticePeriodType.THIRTY_DAYS.value
                _termination_value = fd.get("termination_input", _termination_default)
                if _termination_value not in _termination_options:
                    _termination_value = _termination_default
                with ui.element('div').classes(form_row):
                    with ui.column().classes(form_field):
                        termination_input = ui.select(
                            options=_termination_options,
                            value=_termination_value,
                            label="Termination Notice Period*",
                        ).classes(input_classes).props("outlined").bind_value(
                            fd, "termination_input"
                        )
                        termination_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
                        def validate_termination(e=None):
                            value = termination_input.value or ''
                            if not value.strip() or value not in _termination_options:
                                termination_error.text = (
                                    "Please provide the Termination Notice Period"
                                )
                                termination_error.style('display:block')
                                termination_input.classes('border border-red-600')
                                return False
                            else:
                                termination_error.text = ''
                                termination_error.style('display:none')
                                termination_input.classes(remove='border border-red-600')
                                return True
                        termination_input.on('blur', validate_termination)
                    with ui.column().classes(form_field):
                        with ui.input(
                            label="End date*",
                            placeholder="MM/DD/YYYY",
                            value=fd.get('end_date', '08/24/2025'),
                        ).classes(input_classes).props("outlined").bind_value(
                            fd, "end_date"
                        ) as end_date:
                            with ui.menu().props('no-parent-event') as end_menu:
                                with ui.date(value='2025-08-24').props('mask=MM/DD/YYYY').bind_value(end_date,
                                    forward=lambda d: d.replace('-', '/') if d else '', 
                                    backward=lambda d: d.replace('/', '-') if d else ''):
                                    with ui.row().classes('justify-end'):
                                        ui.button('Close', on_click=end_menu.close).props('flat')
                            with end_date.add_slot('append'):
                                ui.icon('edit_calendar').on('click', end_menu.open).classes('cursor-pointer')
                
                # Row 2 - Automatic Renewal & Expiration Reminder Notice
                with ui.element('div').classes(form_row):
                    with ui.column().classes(form_field):
                        auto_renewal_options = ["Please select", "Yes", "No"]
                        auto_renewal_select = ui.select(
                            options=auto_renewal_options,
                            value=fd.get('auto_renewal_select', "Please select"),
                            label="Automatic renewal*",
                        ).classes(input_classes).props("outlined use-input").bind_value(
                            fd, "auto_renewal_select"
                        )
                        auto_renewal_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
                        
                        # Renewal Period field (conditionally shown)
                        renewal_period_options = ["Please select", "1 Year", "2 Years", "3 Years"]
                        renewal_period_select = ui.select(
                            options=renewal_period_options,
                            value=fd.get('renewal_period_select', "Please select"),
                            label="Renewal term*",
                        ).classes(input_classes + " mt-2").props(
                            "outlined use-input"
                        ).bind_value(fd, "renewal_period_select")
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
                        # Restore renewal period visibility from persisted auto_renewal selection
                        if auto_renewal_select.value == "Yes":
                            renewal_period_select.set_visibility(True)
                        
                    with ui.column().classes(form_field):
                        _expiration_options = [e.value for e in ExpirationNoticePeriodType]
                        _expiration_default = (
                            ExpirationNoticePeriodType.THIRTY_DAYS.value
                        )
                        _expiration_value = fd.get(
                            "expiration_input", _expiration_default
                        )
                        if _expiration_value not in _expiration_options:
                            _expiration_value = _expiration_default
                        expiration_input = ui.select(
                            options=_expiration_options,
                            value=_expiration_value,
                            label="Expiration Date Notice Frequency*",
                        ).classes(input_classes).props("outlined").bind_value(
                            fd, "expiration_input"
                        )
                        expiration_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
                        def validate_expiration(e=None):
                            value = expiration_input.value or ''
                            if not value.strip() or value not in _expiration_options:
                                expiration_error.text = (
                                    "Please provide the Expiration Notice Alert Frequency"
                                )
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
                with ui.element('div').classes(form_row):
                    with ui.column().classes(form_field):
                        contract_type_select = ui.select(
                            options=[
                                "Service Agreement", "Maintenance Contract", "Software License",
                                "Consulting Agreement", "Support Contract", "Lease Agreement",
                                "Purchase Agreement", "Non-Disclosure Agreement", "Partnership Agreement",
                                "Outsourcing Agreement",
                            ],
                            label="Type*",
                            value=fd.get('contract_type_select'),
                        ).classes(input_classes).props("outlined").bind_value(
                            fd, "contract_type_select"
                        )
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
                    with ui.column().classes(form_field):
                        _currency_options = ["Please select", "AWG", "XCG", "USD", "EUR"]
                        _currency_codes = {"AWG", "XCG", "USD", "EUR"}
                        _currency_value = fd.get("currency_select")
                        if _currency_value not in _currency_codes:
                            _currency_value = "Please select"
                        currency_select = ui.select(
                            options=_currency_options,
                            label="Contract Currency*",
                            value=_currency_value,
                        ).classes(input_classes).props("outlined").bind_value(
                            fd, "currency_select"
                        )
                        currency_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
                        def validate_currency(e=None):
                            value = currency_select.value or ''
                            if (
                                not value.strip()
                                or value == "Please select"
                                or value == "Please Select"
                            ):
                                currency_error.text = (
                                    "Please select the Contract Currency"
                                )
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
                with ui.element('div').classes(form_row):
                    with ui.column().classes(form_field):
                        _department_options = [d.value for d in DepartmentType]
                        department_select = ui.select(
                            options=_department_options,
                            label="Department*",
                            value=fd.get('department_select'),
                        ).classes(input_classes).props(
                            "outlined use-input clearable input-debounce=0 "
                            'placeholder="Search departments"'
                        ).bind_value(fd, "department_select")
                        department_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
                        def validate_department(e=None):
                            value = department_select.value or ''
                            if (
                                not str(value).strip()
                                or value == "Please Select"
                                or value not in _department_options
                            ):
                                department_error.text = "Please select a department."
                                department_error.style('display:block')
                                department_select.classes('border border-red-600')
                                return False
                            else:
                                department_error.text = ''
                                department_error.style('display:none')
                                department_select.classes(remove='border border-red-600')
                                return True
                        department_select.on('blur', validate_department)
                    with ui.column().classes(form_field):
                        contract_amount_input = ui.input(
                            label="Amount*",
                            placeholder="e.g. 50000",
                            value=fd.get("contract_amount_input", ""),
                        ).classes(input_classes).props(
                            "outlined maxlength=20"
                        ).bind_value(fd, "contract_amount_input")
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

                # Row 5 - Contract start date & sub-contractor
                with ui.element('div').classes(form_row):
                    with ui.column().classes(form_field):
                        with ui.input(
                            label="Start date*",
                            placeholder="MM/DD/YYYY",
                            value=fd.get('start_date', '08/24/2025'),
                        ).classes(input_classes).props("outlined").bind_value(
                            fd, "start_date"
                        ) as start_date:
                            with ui.menu().props('no-parent-event') as start_menu:
                                with ui.date(value='2025-08-24').props('mask=MM/DD/YYYY').bind_value(start_date, 
                                    forward=lambda d: d.replace('-', '/') if d else '', 
                                    backward=lambda d: d.replace('/', '-') if d else ''):
                                    with ui.row().classes('justify-end'):
                                        ui.button('Close', on_click=start_menu.close).props('flat')
                            with start_date.add_slot('append'):
                                ui.icon('edit_calendar').on('click', start_menu.open).classes('cursor-pointer')
                    with ui.column().classes(form_field):
                        subcontractor_input = ui.input(
                            label="Sub-contractor*",
                            placeholder="Name or N/A",
                            value=fd.get("subcontractor_input", ""),
                        ).classes(input_classes).props(
                            "outlined maxlength=60"
                        ).bind_value(fd, "subcontractor_input")
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
                with ui.element('div').classes(form_row):
                    with ui.column().classes(form_field):
                        notify_options = ["Please select", "Yes", "No"]
                        notify_select = ui.select(
                            options=notify_options,
                            label="Notify before end date?*",
                            value=fd.get("notify_select"),
                        ).classes(input_classes).props("outlined").bind_value(
                            fd, "notify_select"
                        )
                        notify_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
                        def validate_notify(e=None):
                            value = notify_select.value or ''
                            if not value.strip() or value in (
                                "Please select",
                                "Please Select",
                            ):
                                notify_error.text = (
                                    "Please choose Yes or No for end-of-contract notifications."
                                )
                                notify_error.style('display:block')
                                notify_select.classes('border border-red-600')
                                return False
                            else:
                                notify_error.text = ''
                                notify_error.style('display:none')
                                notify_select.classes(remove='border border-red-600')
                                return True
                        notify_select.on('blur', validate_notify)
                    with ui.column().classes(form_field):
                        payment_select = ui.select(
                            options=["Invoice", "Standing Order"],
                            label="Payment*",
                            value=fd.get("payment_select"),
                        ).classes(input_classes).props("outlined").bind_value(
                            fd, "payment_select"
                        )
                        payment_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
                        def validate_payment(e=None):
                            value = payment_select.value or ''
                            if not value or not str(value).strip():
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
                with ui.element("div").classes(f"{form_row} mt-8"):
                    with ui.column().classes(form_field):
                        contract_manager_options = list(contract_managers_data.keys())
                        with ui.row().classes(
                            "w-full gap-4 items-end flex-wrap"
                        ):
                            with ui.column().classes("flex-1 min-w-[200px] grow"):
                                contract_manager_select = ui.select(
                                    options=contract_manager_options,
                                    value=fd.get(
                                        'contract_manager_select', "Please select"
                                    ),
                                    label="Contract Manager*",
                                ).classes(input_classes + " w-full").props(
                                    "outlined use-input"
                                ).bind_value(fd, "contract_manager_select")
                            contract_manager_email_wrap = ui.column().classes(
                                "flex-1 min-w-[240px] shrink-0"
                            )
                            with contract_manager_email_wrap:
                                contract_manager_email_display = ui.input(
                                    label="Email",
                                    value="",
                                ).classes(input_classes + " w-full").props(
                                    "outlined readonly"
                                )
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
                        
                        def sync_contract_manager_email(_=None):
                            name = contract_manager_select.value
                            if not name or name == "Please select":
                                contract_manager_email_display.value = ""
                                contract_manager_email_wrap.set_visibility(False)
                            else:
                                contract_manager_email_display.value = (
                                    contract_managers_data.get(name, "") or ""
                                )
                                contract_manager_email_wrap.set_visibility(True)

                        contract_manager_select.on('blur', validate_contract_manager)
                        contract_manager_select.on(
                            'update:model-value', sync_contract_manager_email
                        )
                        sync_contract_manager_email()
                    with ui.column().classes(form_field):
                        comments_input = ui.input(
                            label="Comments*",
                            placeholder="Internal notes",
                            value=fd.get("comments_input", ""),
                        ).classes(input_classes).props(
                            "outlined maxlength=100"
                        ).bind_value(fd, "comments_input")
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
                with ui.element('div').classes(form_row):
                    with ui.column().classes(form_field):
                        contract_owner_options = list(contract_managers_data.keys())
                        with ui.row().classes(
                            "w-full gap-4 items-end flex-wrap"
                        ):
                            with ui.column().classes("flex-1 min-w-[200px] grow"):
                                contract_owner_select = ui.select(
                                    options=contract_owner_options,
                                    value=fd.get(
                                        'contract_owner_select', "Please select"
                                    ),
                                    label="Contract owner*",
                                ).classes(input_classes + " w-full").props(
                                    "outlined use-input"
                                ).bind_value(
                                    fd, "contract_owner_select"
                                )
                            contract_owner_email_wrap = ui.column().classes(
                                "flex-1 min-w-[240px] shrink-0"
                            )
                            with contract_owner_email_wrap:
                                contract_owner_email_display = ui.input(
                                    label="Email",
                                    value="",
                                ).classes(input_classes + " w-full").props(
                                    "outlined readonly"
                                )
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

                        def sync_contract_owner_email(_=None):
                            name = contract_owner_select.value
                            if not name or name == "Please select":
                                contract_owner_email_display.value = ""
                                contract_owner_email_wrap.set_visibility(False)
                            else:
                                contract_owner_email_display.value = (
                                    contract_managers_data.get(name, "") or ""
                                )
                                contract_owner_email_wrap.set_visibility(True)
                        
                        contract_owner_select.on('blur', validate_contract_owner)
                        contract_owner_select.on(
                            'update:model-value', sync_contract_owner_email
                        )
                        sync_contract_owner_email()
                    with ui.column().classes(form_field):
                        attention_input = ui.input(
                            label="Attention*",
                            placeholder="Addressee",
                            value=fd.get("attention_input", ""),
                        ).classes(input_classes).props(
                            "outlined maxlength=100"
                        ).bind_value(fd, "attention_input")
                        attention_error = ui.label('').classes('text-red-600 text-xs mt-1 min-h-[18px]').style('display:none')
                        def validate_attention(e=None):
                            value = attention_input.value or ''
                            if not value.strip():
                                attention_error.text = (
                                    "Please enter who correspondence should be directed to."
                                )
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
                with ui.element('div').classes(form_row):
                    with ui.column().classes(form_field):
                        contract_backup_options = list(contract_managers_data.keys())
                        with ui.row().classes(
                            "w-full gap-4 items-end flex-wrap"
                        ):
                            with ui.column().classes("flex-1 min-w-[200px] grow"):
                                contract_backup_select = ui.select(
                                    options=contract_backup_options,
                                    value=fd.get(
                                        'contract_backup_select', "Please select"
                                    ),
                                    label="Owner backup*",
                                ).classes(input_classes + " w-full").props(
                                    "outlined use-input"
                                ).bind_value(
                                    fd, "contract_backup_select"
                                )
                            contract_backup_email_wrap = ui.column().classes(
                                "flex-1 min-w-[240px] shrink-0"
                            )
                            with contract_backup_email_wrap:
                                contract_backup_email_display = ui.input(
                                    label="Email",
                                    value="",
                                ).classes(input_classes + " w-full").props(
                                    "outlined readonly"
                                )
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

                        def sync_contract_backup_email(_=None):
                            name = contract_backup_select.value
                            if not name or name == "Please select":
                                contract_backup_email_display.value = ""
                                contract_backup_email_wrap.set_visibility(False)
                            else:
                                contract_backup_email_display.value = (
                                    contract_managers_data.get(name, "") or ""
                                )
                                contract_backup_email_wrap.set_visibility(True)
                        
                        contract_backup_select.on('blur', validate_contract_backup)
                        contract_backup_select.on(
                            'update:model-value', sync_contract_backup_email
                        )
                        sync_contract_backup_email()
                    with ui.column().classes(form_field):
                        upload_details_input = ui.input(
                            label="Other files note (optional)",
                            placeholder="Optional",
                            value=fd.get("upload_details_input", ""),
                        ).classes(input_classes).props("outlined").bind_value(
                            fd, "upload_details_input"
                        )
                
                # Row 10.3 - Vendor Contract (left) & Attachments (right)
                upload_row = (
                    "grid grid-cols-1 md:grid-cols-2 gap-8 items-start w-full"
                )
                with ui.element("div").classes(upload_row):
                    with ui.column().classes(f"{form_field} w-full min-w-0"):
                        vendor_contract_file_display = ui.element("div").classes(
                            "w-full mt-2 flex flex-col gap-3 hidden"
                        )

                        def remove_vendor_contract_doc(doc_uid: str):
                            doc = next(
                                (
                                    d
                                    for d in vendor_contract_docs
                                    if d["uid"] == doc_uid
                                ),
                                None,
                            )
                            if not doc:
                                return
                            doc["row_el"].delete()
                            vendor_contract_docs[:] = [
                                d for d in vendor_contract_docs if d["uid"] != doc_uid
                            ]
                            if not vendor_contract_docs:
                                vendor_contract_file_display.classes(add="hidden")

                        async def handle_vendor_contract_upload(e):
                            if not hasattr(e, "file") or not e.file:
                                ui.notify("No file selected", type="negative")
                                return

                            uploaded_file = e.file
                            file_name = (
                                uploaded_file.name
                                if hasattr(uploaded_file, "name")
                                else "contract.pdf"
                            )
                            if not file_name.lower().endswith(".pdf"):
                                ui.notify(
                                    "Only PDF files are allowed", type="negative"
                                )
                                return

                            file_content = await uploaded_file.read()
                            doc_uid = uuid.uuid4().hex[:12]
                            vendor_contract_file_display.classes(remove="hidden")

                            def validate_rename_input(ren_inp):
                                def _validate(_e=None):
                                    value = ren_inp.value or ""
                                    if value and not re.match(
                                        r"^[a-zA-Z0-9\s\-\|&]*$", value
                                    ):
                                        cleaned = re.sub(
                                            r"[^a-zA-Z0-9\s\-\|&]", "", value
                                        )
                                        ren_inp.value = cleaned
                                        ui.notify(
                                            "Only letters, numbers, and special characters (-, |, &) are allowed",
                                            type="warning",
                                        )

                                return _validate

                            with vendor_contract_file_display:
                                row_wrap = ui.element("div").classes("w-full")
                                with row_wrap:
                                    with ui.card().classes("p-3 bg-blue-50 w-full"):
                                        with ui.row().classes(
                                            "items-start justify-between gap-2 mb-2 w-full"
                                        ):
                                            with ui.row().classes(
                                                "items-center gap-2 min-w-0 flex-1"
                                            ):
                                                ui.icon(
                                                    "picture_as_pdf",
                                                    color="red",
                                                    size="md",
                                                )
                                                ui.label(f"File: {file_name}").classes(
                                                    "text-sm font-medium truncate"
                                                )
                                            ui.button(
                                                icon="close",
                                                on_click=lambda u=doc_uid: remove_vendor_contract_doc(
                                                    u
                                                ),
                                            ).props("flat dense round").classes(
                                                "text-gray-500 shrink-0"
                                            )

                                        rename_input = ui.input(
                                            label="Document name*",
                                            value=file_name.replace(".pdf", ""),
                                            placeholder="A-Z, 0-9, - | &",
                                        ).classes(input_classes + " mb-2").props(
                                            "outlined"
                                        )
                                        rename_input.on(
                                            "input", validate_rename_input(rename_input)
                                        )

                                        with ui.input(
                                            label="Signed date*",
                                            placeholder="MM/DD/YYYY",
                                        ).classes(input_classes).props("outlined") as date_input:
                                            with ui.menu().props(
                                                "no-parent-event"
                                            ) as date_menu:
                                                with ui.date().props(
                                                    "mask=MM/DD/YYYY"
                                                ).bind_value(
                                                    date_input,
                                                    forward=lambda d: d.replace(
                                                        "-", "/"
                                                    )
                                                    if d
                                                    else "",
                                                    backward=lambda d: d.replace(
                                                        "/", "-"
                                                    )
                                                    if d
                                                    else "",
                                                ):
                                                    with ui.row().classes(
                                                        "justify-end"
                                                    ):
                                                        ui.button(
                                                            "Close",
                                                            on_click=date_menu.close,
                                                        ).props("flat")
                                            with date_input.add_slot("append"):
                                                ui.icon(
                                                    "edit_calendar"
                                                ).on(
                                                    "click", date_menu.open
                                                ).classes("cursor-pointer")

                            vendor_contract_docs.append(
                                {
                                    "uid": doc_uid,
                                    "file_bytes": file_content,
                                    "original_name": file_name,
                                    "rename_input": rename_input,
                                    "date_input": date_input,
                                    "row_el": row_wrap,
                                }
                            )

                            vendor_contract_error.text = ""
                            vendor_contract_error.style("display:none")
                            vendor_contract_upload.classes(remove="border border-red-600")
                            ui.notify("PDF file uploaded successfully", type="positive")

                        vendor_contract_upload = ui.upload(
                            on_upload=handle_vendor_contract_upload,
                            auto_upload=True,
                            label="Signed contract PDF*",
                        ).props("accept=.pdf color=primary outlined").classes(
                            "w-full min-h-[140px]"
                        )

                        vendor_contract_error = ui.label("").classes(
                            "text-red-600 text-xs mt-1 min-h-[18px]"
                        ).style("display:none")

                        def validate_vendor_contract(_e=None):
                            for d in vendor_contract_docs:
                                ren = d.get("rename_input")
                                dat = d.get("date_input")
                                if ren:
                                    ren.classes(remove="border border-red-600")
                                if dat:
                                    dat.classes(remove="border border-red-600")

                            if not vendor_contract_docs:
                                vendor_contract_error.text = (
                                    "Please upload this required document"
                                )
                                vendor_contract_error.style("display:block")
                                vendor_contract_upload.classes(
                                    "border border-red-600"
                                )
                                return False

                            for d in vendor_contract_docs:
                                rename_input = d.get("rename_input")
                                date_input = d.get("date_input")
                                rename_value = (
                                    (rename_input.value or "")
                                    if rename_input
                                    else ""
                                )
                                if not rename_value.strip():
                                    vendor_contract_error.text = (
                                        "Please enter a document name"
                                    )
                                    vendor_contract_error.style("display:block")
                                    if rename_input:
                                        rename_input.classes(
                                            "border border-red-600"
                                        )
                                    return False
                                if not re.match(
                                    r"^[a-zA-Z0-9\s\-\|&]+$", rename_value
                                ):
                                    vendor_contract_error.text = (
                                        "Document name can only contain letters, numbers, and special characters: -, |, &"
                                    )
                                    vendor_contract_error.style("display:block")
                                    if rename_input:
                                        rename_input.classes(
                                            "border border-red-600"
                                        )
                                    return False

                                date_value = (
                                    (date_input.value or "") if date_input else ""
                                )
                                if not date_value.strip():
                                    vendor_contract_error.text = (
                                        "Please enter the document date signed"
                                    )
                                    vendor_contract_error.style("display:block")
                                    if date_input:
                                        date_input.classes(
                                            "border border-red-600"
                                        )
                                    return False

                            vendor_contract_error.text = ""
                            vendor_contract_error.style("display:none")
                            vendor_contract_upload.classes(
                                remove="border border-red-600"
                            )
                            return True
                    
                    # gap-0 + upload first: avoids flex gap above an empty list stealing vertical alignment
                    with ui.column().classes("flex flex-col gap-0 w-full min-w-0"):
                        async def handle_upload(e):
                            # NiceGUI upload event has e.file (async SmallFileUpload object)
                            if hasattr(e, 'file') and e.file:
                                uploaded_file = e.file
                                file_name = (
                                    uploaded_file.name
                                    if hasattr(uploaded_file, 'name')
                                    else 'attachment'
                                )

                                # Read file content asynchronously
                                await uploaded_file.read()

                                with uploaded_files_container:
                                    with ui.card().classes(
                                        "p-1 bg-blue-50 flex gap-1 items-center"
                                    ):
                                        ui.icon("attach_file", size="xs").classes(
                                            "text-[#144c8e]"
                                        )
                                        ui.label(file_name).classes("text-xs")
                                        ui.icon("close", size="xs").classes(
                                            "cursor-pointer text-gray-500 hover:text-red-500"
                                        )

                                ui.notify(f'File uploaded: {file_name}', type='positive')
                            else:
                                ui.notify('No file uploaded', type='negative')

                        ui.upload(
                            on_upload=handle_upload,
                            auto_upload=True,
                            multiple=False,
                            label="Other attachments (optional)",
                        ).props("accept=*/* color=primary outlined").classes(
                            "w-full min-h-[140px]"
                        )

                        uploaded_files_container = ui.element("div").classes(
                            "flex flex-col gap-1 w-full mt-2"
                        )

                # Add Submit and Cancel buttons at the bottom
                with ui.element("div").classes("flex justify-center gap-4 mt-8 w-full").props(f'id="c225"'):
                    def clear_contract_form():
                        """Reset all contract form fields to their defaults"""
                        fd.clear()  # Clear persisted form data
                        vendor_select.value = vendor_names[0] if vendor_names else None
                        desc_input.value = ""
                        termination_input.value = NoticePeriodType.THIRTY_DAYS.value
                        expiration_input.value = (
                            ExpirationNoticePeriodType.THIRTY_DAYS.value
                        )
                        auto_renewal_select.value = "Please select"
                        renewal_period_select.value = "Please select"
                        renewal_period_select.set_visibility(False)
                        contract_type_select.value = None
                        currency_select.value = "Please select"
                        department_select.value = None
                        contract_amount_input.value = ""
                        start_date.value = "08/24/2025"
                        end_date.value = "08/24/2025"
                        subcontractor_input.value = ""
                        payment_select.value = None
                        comments_input.value = ""
                        notify_select.value = "Please select"
                        attention_input.value = ""
                        contract_manager_select.value = "Please select"
                        contract_manager_email_display.value = ""
                        contract_manager_email_wrap.set_visibility(False)
                        contract_owner_select.value = "Please select"
                        contract_owner_email_display.value = ""
                        contract_owner_email_wrap.set_visibility(False)
                        contract_backup_select.value = "Please select"
                        contract_backup_email_display.value = ""
                        contract_backup_email_wrap.set_visibility(False)
                        upload_details_input.value = ""
                        for d in vendor_contract_docs:
                            d["row_el"].delete()
                        vendor_contract_docs.clear()
                        vendor_contract_file_display.classes(add="hidden")
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
                            "termination_notice_period": termination_input.value,
                            "expiration_notice_frequency": expiration_input.value,
                            "automatic_renewal": auto_renewal_select.value,
                            "renewal_period": renewal_period_select.value if auto_renewal_select.value == "Yes" else None,
                            "contract_owner_id": owner_id,
                            "contract_owner_backup_id": backup_id,
                            "contract_owner_manager_id": manager_id
                        }
                        
                        # Prepare form data for API (matching vendors pattern)
                        api_host = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
                        url = f"{api_host}{settings.api_v1_prefix}/contracts/"
                        
                        if not vendor_contract_docs:
                            ui.notify(
                                "Please upload the vendor contract document",
                                type="negative",
                            )
                            return

                        first = vendor_contract_docs[0]
                        doc_name = (first["rename_input"].value or "").strip()
                        doc_date = (
                            convert_date(first["date_input"].value)
                            if first.get("date_input")
                            else None
                        )
                        if not doc_date:
                            ui.notify(
                                "Please enter the document signed date",
                                type="negative",
                            )
                            return

                        files = {
                            "contract_data": (None, json.dumps(contract_data)),
                            "document_name": (None, doc_name),
                            "document_signed_date": (None, doc_date),
                            "contract_document": (
                                "contract.pdf",
                                first["file_bytes"],
                                "application/pdf",
                            ),
                        }
                        
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
                                    contract_db_id = result.get("id")

                                    extra_upload_failures = []
                                    if (
                                        contract_db_id is not None
                                        and len(vendor_contract_docs) > 1
                                    ):
                                        docs_url = (
                                            f"{api_host}{settings.api_v1_prefix}"
                                            f"/contracts/{contract_db_id}/documents"
                                        )
                                        for item in vendor_contract_docs[1:]:
                                            nm = (
                                                item["rename_input"].value or ""
                                            ).strip()
                                            dt = convert_date(
                                                item["date_input"].value
                                            )
                                            extra_files = {
                                                "document_name": (None, nm),
                                                "document_signed_date": (
                                                    None,
                                                    dt,
                                                ),
                                                "file": (
                                                    f"{nm}.pdf",
                                                    item["file_bytes"],
                                                    "application/pdf",
                                                ),
                                            }
                                            r2 = await client.post(
                                                docs_url, files=extra_files
                                            )
                                            if r2.status_code not in (200, 201):
                                                extra_upload_failures.append(
                                                    r2.text[:300]
                                                )

                                    if extra_upload_failures:
                                        ui.notify(
                                            f'Contract "{contract_id}" was created, but '
                                            f"{len(extra_upload_failures)} additional PDF(s) "
                                            "failed to upload. Add them from the contract record.",
                                            type="warning",
                                            position="top",
                                            close_button=True,
                                            timeout=10000,
                                        )
                                    else:
                                        ui.notify(
                                            f'✅ SUCCESS! Contract "{contract_id}" created successfully!',
                                            type="positive",
                                            position="top",
                                            close_button=True,
                                            timeout=5000,
                                        )
                                    print(f"✅ Contract created: {contract_id}")
                                    clear_contract_form()
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
            
           