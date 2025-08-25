from nicegui import ui


def header():
    ui.link.default_classes(
        "no-underline text-base text-gray-500 items-center text-normal hover:underline font-[segoe ui] hover:text-black"
    )
    ui.dropdown_button.default_classes(
        "text-weight-regular normal-case text-gray-500 font-[segoe ui]"
    ).default_props("flat")
    with (
        ui.header()
        .classes(
            "bg-[#f8f9fa] p-2 font-[segoe ui] items-center flex flex-row justify-between"
        )
        .props("flat")
    ):
        # Left section: logo, navbar, dropdowns
        with ui.element("div").classes("flex flex-row items-center gap-3"):
            ui.link("Aruba Bank", "/").classes(
                "font-bold text-xl text-center mt-3 text-black w-32 h-[39px]"
            )
            ui.link("Home", "/").classes("text-black")
            ui.link("New Contract", "/new-contract")
            ui.link("New Vendor", "/new-vendor")
            with (
                ui.dropdown_button("Reports", auto_close=True, color=None)
                .classes(
                    "text-weight-regular normal-case text-gray-500 font-[segoe ui]"
                )
                .props("flat")
            ):
                ui.link("Active agreements", "/active-contracts").classes(
                    "text-black font-[segoe ui] flex flex-column p-2"
                )
                ui.link("Pending agreements", "/pending-contracts").classes(
                    "text-black font-[segoe ui] flex flex-column p-2"
                )
                ui.link("Expired agreements", "/expired-contracts").classes(
                    "text-black font-[segoe ui] flex flex-column p-2"
                )
                ui.link("Terminated agreements", "/terminated-contracts").classes(
                    "text-black font-[segoe ui] flex flex-column p-2"
                )
                ui.menu_item("Audit trail").classes(
                    "text-black font-[segoe ui] flex flex-column p-2 border-t border-gray-200"
                )

            with (
                ui.dropdown_button("Advanced search", color=None)
                .props("flat")
                .classes(
                    "text-weight-regular normal-case text-gray-500 font-[segoe ui]"
                )
            ):
                with ui.column().classes("gap-2 p-2 min-w-[320px]"):
                    # Search mode
                    ui.label("Search mode").classes("text-xs font-semibold text-gray-700")
                    ui.select(["AND", "OR"], value="AND").classes("w-full")
                    # Contract ID
                    ui.label("Contract ID:").classes("text-xs font-semibold text-gray-700")
                    ui.input(placeholder="Enter contract ID").classes("w-full")
                    # Vendor
                    ui.label("Vendor:").classes("text-xs font-semibold text-gray-700")
                    ui.select(["Select a Vendor", "ABC Corp", "XYZ Services", "Acme Ltd"], value="Select a Vendor").classes("w-full")
                    # Type of Contract
                    ui.label("Type of Contract:").classes("text-xs font-semibold text-gray-700")
                    ui.select(["Select a contract type", "Service", "Supply", "Consulting"], value="Select a contract type").classes("w-full")
                    # Department
                    ui.label("Department:").classes("text-xs font-semibold text-gray-700")
                    ui.select(["Select a department", "Finance", "HR", "IT", "Legal"], value="Select a department").classes("w-full")
                    # Contract Start Date
                    ui.label("Contract Start Date:").classes("text-xs font-semibold text-gray-700")
                    with ui.input('Date') as date:
                        with ui.menu().props('no-parent-event') as menu:
                            with ui.date().bind_value(date):
                                with ui.row().classes('justify-end'):
                                    ui.button('Close', on_click=menu.close).props('flat')
                        with date.add_slot('append'):
                            ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer')
                    # Contract Expiration Date
                    ui.label("Contract Expiration Date:").classes("text-xs font-semibold text-gray-700")
                    with ui.input('Date') as exp_date:
                        with ui.menu().props('no-parent-event') as menu:
                            with ui.date().bind_value(exp_date):
                                with ui.row().classes('justify-end'):
                                    ui.button('Close', on_click=menu.close).props('flat')
                        with exp_date.add_slot('append'):
                            ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer')
                    # Buttons
                    with ui.row().classes("gap-2 pt-2"):
                        ui.button("Search", color="primary").classes("w-24")
                        ui.button("Clear", color=None).classes("w-24")

        # Spacer to push right section to the end
        ui.element("div").classes("flex-grow")

        # Right section: search input and logout button
        with ui.element("div").classes("flex flex-row items-center gap-4"):
            ui.input(placeholder="Search").classes(
                "w-64 bg-white font-[segoe ui]"
            ).props("outlined dense")
            ui.button("Logout", color=None, icon="logout").classes(
                "text-weight-regular normal-case text-gray-500 font-[segoe ui]"
            ).props("flat")
