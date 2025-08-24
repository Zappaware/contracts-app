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
        ui.select(options=vendors, value=vendors[0], label="Select vendor").classes(
            "w-64 mt-8 font-[segoe ui]"
        ).props("outlined")
        ui.input(label="Contract description or purpose").classes(
            "w-1/2 mt-4 font-[segoe ui]"
        ).props("outlined")
