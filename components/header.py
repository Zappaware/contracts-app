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
                ui.menu_item("Active agreements").classes(
                    "text-black font-[segoe ui] flex flex-column p-2"
                )
                ui.menu_item("Pending agreements").classes(
                    "text-black font-[segoe ui] flex flex-column p-2"
                )
                ui.menu_item("Expired agreements").classes(
                    "text-black font-[segoe ui] flex flex-column p-2"
                )
                ui.menu_item("Terminated agreements").classes(
                    "text-black font-[segoe ui] flex flex-column p-2"
                )
                ui.menu_item("Audit trail").classes(
                    "text-black font-[segoe ui] flex flex-column p-2 border-t border-gray-200"
                )

            with (
                ui.dropdown_button("Advanced search", auto_close=True, color=None)
                .props("flat")
                .classes(
                    "text-weight-regular normal-case text-gray-500 font-[segoe ui]"
                )
            ):
                ui.menu_item("Search Vendors").classes(
                    "text-black font-[segoe ui] flex flex-column p-2"
                )
                ui.menu_item("Search Contracts").classes(
                    "text-black font-[segoe ui] flex flex-column p-2"
                )

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
