from nicegui import ui

from components.header import header
from components.home_page import home_page


@ui.page("/")
def main_page():
    header()
    home_page()


@ui.page("/new-vendor")
def new_vendor_page():
    header()
    ui.label("New Vendor Page - Under Construction")


@ui.page("/new-contract")
def new_contract_page():
    header()
    ui.label("New Contract Page - Under Construction")


ui.run(title="Aruba Bank", port=5000)
