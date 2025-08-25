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
        
        # Add contract details section as a div-based table with 4 columns
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
                
                # Row 1 - ID & Termination Notice
                with ui.element('div').classes(f"{row_classes} {std_row_height}"):
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("ID").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        ui.label("ID").classes(input_classes)
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Termination Notice").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        ui.input(label="Days", value="30").props("type=number").classes(input_classes).props("outlined")
                
                # Row 2 - Automatic Renewal & Expiration Reminder Notice
                with ui.element('div').classes(f"{row_classes} {std_row_height}"):
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Automatic Renewal?").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        with ui.element("div").classes("py-1"):
                            ui.switch("Yes")
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Expiration Reminder Notice").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        ui.input(label="Days", value="30").props("type=number").classes(input_classes).props("outlined")
                
                # Row 3 - Type of Contract & Currency
                with ui.element('div').classes(f"{row_classes} {std_row_height}"):
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Type of Contract").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        ui.select(options=["Advertising", "Publicity", "Account"], label="Please Select").classes(input_classes).props("outlined")
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Currency").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        ui.select(options=["USD", "EUR", "GBP", "JPY", "CAD"], label="Please Select").classes(input_classes).props("outlined")
                
                # Row 4 - Department & Initial Fee
                with ui.element('div').classes(f"{row_classes} {std_row_height}"):
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Department").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        ui.select(options=["Business Continuity", "Certificates", "Organizations"], label="Please Select").classes(input_classes).props("outlined")
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Initial Fee").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        ui.input(label="Do not Format it", value="0.00").props("disabled").classes(input_classes).props("outlined")

                # Row 5 - Contract Start Date & Sub-contractor's name
                with ui.element('div').classes(f"{row_classes} {std_row_height}"):
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Contract Start Date").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        with ui.input('MM/DD/YYYY', value='08/24/2025').classes(input_classes).props("outlined") as start_date:
                            with ui.menu().props('no-parent-event') as start_menu:
                                with ui.date(value='2025-08-24').props('mask=MM/DD/YYYY').bind_value(start_date, 
                                    forward=lambda d: d.replace('-', '/') if d else '', 
                                    backward=lambda d: d.replace('/', '-') if d else ''):
                                    with ui.row().classes('justify-end'):
                                        ui.button('Close', on_click=start_menu.close).props('flat')
                            with start_date.add_slot('append'):
                                ui.icon('edit_calendar').on('click', start_menu.open).classes('cursor-pointer')
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Sub-contractor's name").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        ui.input().classes(input_classes).props("outlined")
                
                # Row 6 - Contract Expiration Date & Maintenance Fee
                with ui.element('div').classes(f"{row_classes} {std_row_height}"):
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Contract Expiration Date").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        with ui.input('MM/DD/YYYY', value='08/24/2025').classes(input_classes).props("outlined") as end_date:
                            with ui.menu().props('no-parent-event') as end_menu:
                                with ui.date(value='2025-08-24').props('mask=MM/DD/YYYY').bind_value(end_date,
                                    forward=lambda d: d.replace('-', '/') if d else '', 
                                    backward=lambda d: d.replace('/', '-') if d else ''):
                                    with ui.row().classes('justify-end'):
                                        ui.button('Close', on_click=end_menu.close).props('flat')
                            with end_date.add_slot('append'):
                                ui.icon('edit_calendar').on('click', end_menu.open).classes('cursor-pointer')
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Maintenance Fee").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        ui.input(label="Do not Format it", value="0.00").props("outlined disable").classes(input_classes)

                # Row 7 - Contract Termination & Payment Method
                with ui.element('div').classes(f"{row_classes} {std_row_height}"):
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Contract Termination").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        with ui.element("div").classes("py-1"):
                            ui.switch("Yes")
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Payment Method").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        ui.select(options=["Credit Card", "Bank Transfer", "Cash", "Check"], label="Please Select").classes(input_classes).props("outlined")

                # Row 8 - Maintenance Terms & Comments
                with ui.element('div').classes(f"{row_classes} {std_row_height}"):
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Maintenance Terms").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        ui.select(options=[], label="Please Select").classes(input_classes).props("outlined")
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Comments").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        ui.textarea().classes("w-full font-[segoe ui] h-12 max-h-12 overflow-y-auto").props("outlined")

                # Row 9 - Notify when Expired? & Attention
                with ui.element('div').classes(f"{row_classes} {std_row_height}"):
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Notify when Expired?").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        ui.select(options=[], label="Please Select").classes(input_classes).props("outlined")
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Attention").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        ui.textarea().classes("w-full font-[segoe ui] h-12 max-h-12 overflow-y-auto").props("outlined")

                # Row 10 - Notification Email Address & Last Revision User
                with ui.element('div').classes(f"{row_classes} {std_row_height}"):
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Notification Email Address").classes(label_classes).props("outlined")
                    with ui.element('div').classes(input_cell_classes):
                        ui.input_chips("Enter email and press Enter", new_value_mode="add").classes(input_classes).props("type=email outlined chips")
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Last Revision User").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        ui.input().classes(input_classes).props("outlined")
                
                # Row 10.5 - File Attachments (right below Notification Email Address)
                with ui.element('div').classes(f"{row_classes} {std_row_height}"):
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Attachments").classes("text-white font-[segoe ui] py-8 px-4 h-full")
                    with ui.element('div').classes(f"{input_cell_classes} pt-4"):
                        with ui.card().classes("w-full h-auto p-0"):
                            
                            def handle_upload(e):
                                for file_name in e.file_names:
                                    with uploaded_files_container:
                                        with ui.card().classes("p-1 bg-blue-50 flex gap-1 items-center"):
                                            ui.icon("attach_file", size="xs").classes("text-[#144c8e]")
                                            ui.label(file_name).classes("text-xs")
                                            ui.icon("close", size="xs").classes("cursor-pointer text-gray-500 hover:text-red-500")
                                ui.notify(f'{len(e.file_names)} file(s) uploaded successfully', type='positive')
                            
                            ui.upload(on_upload=handle_upload, multiple=True, label="Drop files here or click to browse").props('accept=*/* color=primary outlined').classes("w-full")
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Upload Details").classes("text-white font-[segoe ui] py-8 px-4  h-full")
                    with ui.element('div').classes(input_cell_classes):
                        ui.input(label="Description", placeholder="Enter a description for these files").classes(input_classes).props("outlined")
                
                # Row 11 - Empty & Last Revision Date
                with ui.element('div').classes(f"{row_classes} {std_row_height}"):
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        ui.label("").classes(input_classes)
                    with ui.element('div').classes(label_cell_classes):
                        ui.label("Last Revision Date").classes(label_classes)
                    with ui.element('div').classes(input_cell_classes):
                        ui.input().classes(input_classes).props("outlined")


                # Add Submit and Cancel buttons at the bottom
                with ui.element("div").classes("flex justify-end gap-4 mt-8 mr-20 w-full"):
                    ui.button("Cancel", icon="close").props("flat").classes("text-gray-700")
                    ui.button("Submit", icon="check").classes("bg-[#144c8e] text-white")
            
           