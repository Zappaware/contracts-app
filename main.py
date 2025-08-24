from nicegui import ui

from components.header import header
from pages.home_page import home_page
from pages.new_contract import new_contract


@ui.page("/")
def main_page():
    header()
    home_page()


@ui.page("/new-contract")
def new_contract_page():
    header()
    new_contract()


@ui.page("/new-vendor")
def new_vendor_page():
    header()
    ui.label("New Vendor Page - Under Construction")


ui.run(title="Aruba Bank", port=5000)
