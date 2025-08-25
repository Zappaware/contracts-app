from nicegui import ui


def new_vendor():
    with ui.element("div").classes(
        "flex flex-col items-center justify-center mt-8 w-full "
    ):
        ui.input(label="Vendor search", placeholder="Search for existing vendors...").classes("w-1/2 mt-4 font-[segoe ui]").props("outlined")
        ui.button("New Vendor", icon="add").classes("mt-4 bg-[#144c8e] text-white")
        
        # Add vendor details section as a div-based table with 4 columns
        with ui.element("div").classes("w-full border rounded border-gray-300 max-w-7xl mt-8 p-6 mx-auto"):
            # Define style classes as constants to avoid duplication
            label_classes = "text-white font-[segoe ui] py-2 px-4 h-full flex items-center"
            input_classes = "w-full font-[segoe ui]"
            row_classes = "flex w-full"
            std_row_height = "h-16"

            # Cell classes for consistent styling
            label_cell_classes = "bg-[#144c8e] w-[16.6%] flex items-center"
            input_cell_classes = "bg-white p-2 w-[33.3%]"
            
            # Create a custom table-like layout using divs
            with ui.element("div").classes("w-full border-collapse flex flex-col"):
                
                # Row 1 - ID & AB Customer?
                with ui.element('div').classes(f"{row_classes} {std_row_height}"):
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("ID").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        ui.label("ID").classes(input_classes)
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("AB Customer?").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        with ui.element("div").classes("py-1"):
                            ui.switch("Yes")
                
                # Row 2 - Name & Contact Person
                with ui.element('div').classes(f"{row_classes} {std_row_height}"):
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Name").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        ui.input().classes(input_classes).props("outlined")
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Contact Person").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        ui.input().classes(input_classes).props("outlined")
                
                # Row 3 - Address 1 & Address 2
                with ui.element('div').classes(f"{row_classes} {std_row_height}"):
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Address 1").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        ui.input().classes(input_classes).props("outlined")
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Address 2").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        ui.input().classes(input_classes).props("outlined")
                
                # Row 4 - City & State
                with ui.element('div').classes(f"{row_classes} {std_row_height}"):
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("City").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        ui.input().classes(input_classes).props("outlined")
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("State").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        ui.input().classes(input_classes).props("outlined")

                # Row 5 - Zip Code & Country
                with ui.element('div').classes(f"{row_classes} {std_row_height}"):
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Zip Code").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        ui.input().classes(input_classes).props("outlined")
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Country").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        ui.input().classes(input_classes).props("outlined")
                
                # Row 6 - Telephone Number & Email
                with ui.element('div').classes(f"{row_classes} {std_row_height}"):
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Telephone Number").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        ui.input().props("type=tel outlined").classes(input_classes)
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Email").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        ui.input().props("type=email outlined").classes(input_classes)

                # Row 7 - Last Due Diligence Date & Next Required Due Diligence (days)
                with ui.element('div').classes(f"{row_classes} {std_row_height}"):
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Last Due Diligence Date").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        with ui.input('MM/DD/YYYY', value='08/25/2025').classes(input_classes).props("outlined") as due_diligence_date:
                            with ui.menu().props('no-parent-event') as due_diligence_menu:
                                with ui.date(value='2025-08-25').props('mask=MM/DD/YYYY').bind_value(due_diligence_date, 
                                    forward=lambda d: d.replace('-', '/') if d else '', 
                                    backward=lambda d: d.replace('/', '-') if d else ''):
                                    with ui.row().classes('justify-end'):
                                        ui.button('Close', on_click=due_diligence_menu.close).props('flat')
                            with due_diligence_date.add_slot('append'):
                                ui.icon('edit_calendar').on('click', due_diligence_menu.open).classes('cursor-pointer')
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Next Required Due Diligence").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        ui.input(label="Days", value="30").props("type=number outlined").classes(input_classes)

                # Row 8 - Next Due Diligence Alert & Frequency (in days)
                with ui.element('div').classes(f"{row_classes} {std_row_height}"):
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Next Required Due Diligence Alert").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        ui.input(label="Days", value="15").props("type=number outlined").classes(input_classes)
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Frequency (in days)").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        ui.input(label="Days", value="90").props("type=number outlined").classes(input_classes)

                # Row 9 - Due Diligence Upload & Non-Disclosure Agreement Upload
                with ui.element('div').classes(f"{row_classes} h-30"):
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Due Diligence").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        def handle_due_diligence_upload(e):
                            ui.notify(f'Due Diligence document uploaded: {e.file_names[0]}', type='positive')
                        
                        ui.upload(on_upload=handle_due_diligence_upload, multiple=False, label="Upload due diligence").props('accept=.pdf,.doc,.docx color=primary outlined').classes("w-full")
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Non-Disclosure Agreement").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        def handle_nda_upload(e):
                            ui.notify(f'NDA document uploaded: {e.file_names[0]}', type='positive')
                        
                        ui.upload(on_upload=handle_nda_upload, multiple=False, label="Upload NDA").props('accept=.pdf,.doc,.docx color=primary outlined').classes("w-full")

                # Row 10 - Integrity Policy Upload & Risk Assessment Form Upload
                with ui.element('div').classes(f"{row_classes} h-30"):
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Integrity Policy").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        def handle_policy_upload(e):
                            ui.notify(f'Integrity Policy document uploaded: {e.file_names[0]}', type='positive')
                        
                        ui.upload(on_upload=handle_policy_upload, multiple=False, label="Upload policy").props('accept=.pdf,.doc,.docx color=primary outlined').classes("w-full")
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Risk Assessment Form").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        def handle_risk_upload(e):
                            ui.notify(f'Risk Assessment document uploaded: {e.file_names[0]}', type='positive')
                        
                        ui.upload(on_upload=handle_risk_upload, multiple=False, label="Upload form").props('accept=.pdf,.doc,.docx color=primary outlined').classes("w-full")
                
                # Row 11 - Attention (standard size row for description)
                with ui.element('div').classes(f"{row_classes} h-24"):
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Attention").classes(label_classes)
                    with ui.element('div').classes(f"{input_cell_classes} mt-4"):
                        ui.textarea().classes("w-full font-[segoe ui] h-20").props("outlined")
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        ui.label("").classes(input_classes)
                
                # Row 12 - Submit and Cancel buttons inside the table
                with ui.element('div').classes(f"{row_classes} {std_row_height}"):
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        ui.label("").classes(input_classes)
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes + " flex justify-end gap-4"):
                        ui.button("Cancel", icon="close").props("flat").classes("text-gray-700")
                        ui.button("Submit", icon="check").classes("bg-[#144c8e] text-white")
            
           