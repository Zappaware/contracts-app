
from nicegui import ui
import requests


def home_page():
    # Quick Stats Cards (shrink to table width)
    with ui.element("div").classes("max-w-6xl mx-auto w-full"):
        with ui.row().classes(
            "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 mt-8 gap-6 w-full"
        ):
            with ui.card().classes("w-full"):
                ui.label("Active Contracts").classes("text-lg font-bold")
                ui.label("Currently active contracts").classes("text-sm text-gray-500")
                ui.label("1,247").classes("text-2xl font-medium text-primary mt-2")
            with ui.card().classes("w-full"):
                ui.label("Pending Reviews").classes("text-lg font-bold")
                ui.label("Contracts awaiting review").classes("text-sm text-gray-500")
                ui.label("23").classes("text-2xl font-medium text-primary mt-2")
            with ui.card().classes("w-full"):
                ui.label("Total Vendors").classes("text-lg font-bold")
                ui.label("Registered vendors").classes("text-sm text-gray-500")
                ui.label("89").classes("text-2xl font-medium text-primary mt-2")

    # Recent Activity Section (shrink to table width)
    with ui.element("div").classes("max-w-6xl mt-8 mx-auto w-full"):
        with ui.card().classes("mt-8 w-full"):
            ui.label("Recent Activity").classes("text-lg font-bold")
            ui.label("Latest contract management activities").classes(
                "text-sm text-gray-500 mb-4"
            )
            with ui.column().classes("space-y-4 w-full"):
                with ui.row().classes(
                    "flex items-center justify-between py-2 border-b border-gray-200 last:border-b-0 w-full"
                ):
                    with ui.column():
                        ui.label("New contract created").classes("font-medium")
                        ui.label("Contract #CTR-2024-001 with ABC Corp").classes(
                            "text-sm text-gray-500"
                        )
                    ui.label("2 hours ago").classes("text-sm text-gray-500")
                with ui.row().classes(
                    "flex items-center justify-between py-2 border-b border-gray-200 last:border-b-0 w-full"
                ):
                    with ui.column():
                        ui.label("Vendor registered").classes("font-medium")
                        ui.label("XYZ Services added to vendor database").classes(
                            "text-sm text-gray-500"
                        )
                    ui.label("4 hours ago").classes("text-sm text-gray-500")
                with ui.row().classes(
                    "flex items-center justify-between py-2 border-b border-gray-200 last:border-b-0 w-full"
                ):
                    with ui.column():
                        ui.label("Contract approved").classes("font-medium")
                        ui.label(
                            "Contract #CTR-2024-002 approved by management"
                        ).classes("text-sm text-gray-500")
                    ui.label("1 day ago").classes("text-sm text-gray-500")
    with ui.element("div").classes("max-w-6xl mt-8 mx-auto w-full"):
        ui.label("Vendor List").classes("text-h5 ml-4 font-bold ")

    columns = [
        {
            "name": "id",
            "label": "Id",
            "field": "id",
            "align": "left",
        },
        {
            "name": "name",
            "label": "Name",
            "field": "name",
            "align": "left",
        },
        {
            "name": "contact",
            "label": "Contact Person",
            "field": "contact",
            "align": "left",
        },
        {
            "name": "country",
            "label": "Country",
            "field": "country",
            "align": "left",
        },
        {
            "name": "telephone",
            "label": "Telephone",
            "field": "telephone",
            "align": "left",
        },
        {
            "name": "email",
            "label": "Email",
            "field": "email",
            "align": "left",
        },
        {
            "name": "D.D. Performed",
            "label": "D.D. Performed",
            "field": "dd_performed",
            "align": "left",
        },
        {
            "name": "attention",
            "label": "Attention",
            "field": "attention",
            "align": "left",
        },
    ]
    columns_defaults = {
        "align": "left",
        "headerClasses": "bg-[#144c8e] text-white",
    }
    def fetch_vendors():
        url = "http://localhost:8000/api/v1/vendors/"
        try:
            response = requests.get(url)
            response.raise_for_status()
            vendor_list = response.json()
            # Map backend vendor data to table row format
            rows = []
            for v in vendor_list:
                rows.append({
                    "id": v.get("id", ""),
                    "name": v.get("vendor_name", ""),
                    "contact": v.get("vendor_contact_person", ""),
                    "country": v.get("vendor_country", ""),
                    "telephone": v.get("phones", [{}])[0].get("phone_number", "") if v.get("phones") else "",
                    "email": v.get("emails", [{}])[0].get("email", "") if v.get("emails") else "",
                    "dd_performed": "Yes" if v.get("due_diligence_required", "No") == "Yes" else "No",
                    "attention": v.get("attention", "")
                })
            return rows
        except Exception as e:
            ui.notify(f"Error fetching vendors: {e}", type="negative")
            return []

    rows = fetch_vendors()

    with ui.element("div").classes("max-w-6xl mx-auto w-full"):
        ui.table(
            columns=columns, column_defaults=columns_defaults, rows=rows, pagination=3
        ).classes("w-full").props("flat").classes(
            "vendor-table shadow-lg rounded-lg overflow-hidden"
        )
        ui.add_css(".vendor-table thead tr { background-color: #144c8e !important; }")
