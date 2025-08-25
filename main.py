from nicegui import app, ui
from components.header import header
from pages.home_page import home_page
from pages.new_contract import new_contract
from pages.new_vendor import new_vendor
from pages.login import login_page

@ui.page("/")
def main_page():
    if not app.storage.user.get('logged_in'):
        ui.navigate.to('/login')
        return
    header()
    home_page()

@ui.page("/new-contract")
def new_contract_page():
    if not app.storage.user.get('logged_in'):
        ui.navigate('/login')
        return
    header()
    new_contract()

@ui.page("/new-vendor")
def new_vendor_page():
    if not app.storage.user.get('logged_in'):
        ui.navigate('/login')
        return
    header()
    new_vendor()

@ui.page("/login")
def login_route():
    login_page()

ui.run(title="Aruba Bank", port=5000, storage_secret="aruba_bank_secret")
