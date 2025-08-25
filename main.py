from nicegui import app, ui
from components.header import header
from pages.home_page import home_page
from pages.new_contract import new_contract
from pages.new_vendor import new_vendor
from pages.login import login_page
from pages.terminated_contracts import terminated_contracts
from pages.active_contracts import active_contracts
from pages.pending_contracts import pending_contracts
from pages.expired_contracts import expired_contracts


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

@ui.page("/terminated-contracts")
def terminated_contracts_page():
    header()
    terminated_contracts()

@ui.page("/active-contracts")
def active_contracts_page():
    header()
    active_contracts()

@ui.page("/pending-contracts")
def pending_contracts_page():
    header()
    pending_contracts()

@ui.page("/expired-contracts")
def expired_contracts_page():
    header()
    expired_contracts()

ui.run(title="Aruba Bank", port=5000, storage_secret="aruba_bank_secret")
