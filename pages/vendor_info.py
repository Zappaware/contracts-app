

from nicegui import ui

def vendor_info():
    # Basic info
    with ui.card().classes("max-w-3xl mx-auto mt-8 p-6"):
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




