from nicegui import app, ui

def login_page():
    def do_login():
        app.storage.user['logged_in'] = True
        ui.navigate.to('/')
    with ui.element('div').classes('fixed inset-0 flex items-center justify-center bg-gray-50'):
        with ui.card().classes('w-96 p-8 flex flex-col items-center justify-center'):
            ui.label('Aruba Bank').classes('text-3xl font-bold text-[#144c8e] mb-8 text-center')
            ui.input(label='Username').classes('w-full mb-4 text-center').props('outlined')
            ui.input(label='Password', password=True).classes('w-full mb-6 text-center').props('outlined')
            ui.button('Login', on_click=do_login).classes('w-full bg-[#144c8e] text-white')
