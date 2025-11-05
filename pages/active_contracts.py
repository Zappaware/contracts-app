from datetime import datetime, timedelta
from nicegui import ui


def active_contracts():
    # Navigation
    with ui.row().classes("max-w-6xl mx-auto mt-4"):
        with ui.link(target='/').classes('no-underline'):
            ui.button("← Back to Dashboard", icon="arrow_back").props('flat color=primary')
    
    # Global variables for table and data
    contracts_table = None
    contract_rows = []
    
    # Function to handle owned/backup switch toggle (no functionality for now)
    def on_switch_toggle(value):
        if value:
            ui.notify("Owned contracts selected", type="info")
        else:
            ui.notify("Backup contracts selected", type="info")
    
    # Mock data for active contracts
    def get_mock_active_contracts():
        """
        Simulates active contracts.
        This will be replaced with actual API call when available.
        """
        today = datetime.now()
        
        mock_contracts = [
            {
                "contract_id": "CTR-2024-001",
                "vendor_name": "Acme Corp",
                "contract_type": "Service Agreement",
                "description": "IT Support Services",
                "expiration_date": today + timedelta(days=180),
                "manager": "William Defoe",
                "role": "owned"
            },
            {
                "contract_id": "CTR-2024-012",
                "vendor_name": "Beta Technologies",
                "contract_type": "Software License",
                "description": "Enterprise Software Licensing",
                "expiration_date": today + timedelta(days=240),
                "manager": "John Doe",
                "role": "backup"
            },
            {
                "contract_id": "CTR-2024-023",
                "vendor_name": "Gamma Consulting",
                "contract_type": "Consulting",
                "description": "Business Process Optimization",
                "expiration_date": today + timedelta(days=150),
                "manager": "William Defoe",
                "role": "owned"
            },
            {
                "contract_id": "CTR-2024-034",
                "vendor_name": "Delta Logistics",
                "contract_type": "Transportation",
                "description": "Freight and Delivery Services",
                "expiration_date": today + timedelta(days=200),
                "manager": "John Doe",
                "role": "backup"
            },
            {
                "contract_id": "CTR-2023-089",
                "vendor_name": "Epsilon Security",
                "contract_type": "Security Services",
                "description": "Building Security and Monitoring",
                "expiration_date": today + timedelta(days=365),
                "manager": "William Defoe",
                "role": "owned"
            },
            {
                "contract_id": "CTR-2024-045",
                "vendor_name": "Zeta Solutions",
                "contract_type": "Maintenance",
                "description": "Equipment Maintenance Contract",
                "expiration_date": today + timedelta(days=120),
                "manager": "John Doe",
                "role": "backup"
            },
            {
                "contract_id": "CTR-2024-056",
                "vendor_name": "Eta Services",
                "contract_type": "Cleaning Services",
                "description": "Office Cleaning and Janitorial",
                "expiration_date": today + timedelta(days=275),
                "manager": "William Defoe",
                "role": "owned"
            },
            {
                "contract_id": "CTR-2024-067",
                "vendor_name": "Theta Communications",
                "contract_type": "Telecommunications",
                "description": "Internet and Phone Services",
                "expiration_date": today + timedelta(days=300),
                "manager": "John Doe",
                "role": "backup"
            },
        ]
        
        rows = []
        for contract in mock_contracts:
            exp_date = contract["expiration_date"]
            
            rows.append({
                "contract_id": contract["contract_id"],
                "vendor_name": contract["vendor_name"],
                "contract_type": contract["contract_type"],
                "description": contract["description"],
                "expiration_date": exp_date.strftime("%Y-%m-%d"),
                "expiration_timestamp": exp_date.timestamp(),  # For sorting
                "status": "Active",
                "manager": contract["manager"],
                "role": contract["role"],
            })
        
        return rows

    contract_columns = [
        {
            "name": "contract_id",
            "label": "Contract ID",
            "field": "contract_id",
            "align": "left",
            "sortable": True,
        },
        {
            "name": "vendor_name",
            "label": "Vendor Name",
            "field": "vendor_name",
            "align": "left",
            "sortable": True,
        },
        {
            "name": "contract_type",
            "label": "Contract Type",
            "field": "contract_type",
            "align": "left",
            "sortable": True,
        },
        {
            "name": "description",
            "label": "Contract Description",
            "field": "description",
            "align": "left",
        },
        {
            "name": "expiration_date",
            "label": "Expiration Date",
            "field": "expiration_date",
            "align": "left",
            "sortable": True,
            "sort-order": "ad",  # Ascending/Descending
        },
        {
            "name": "status",
            "label": "Status",
            "field": "status",
            "align": "left",
        },
        {
            "name": "manager",
            "label": "Manager",
            "field": "manager",
            "align": "left",
            "sortable": True,
        },
    ]

    contract_columns_defaults = {
        "align": "left",
        "headerClasses": "bg-[#144c8e] text-white",
    }

    contract_rows = get_mock_active_contracts()
    
    # Main container
    with ui.element("div").classes("max-w-6xl mt-8 mx-auto w-full"):
        # Section header with switch
        with ui.row().classes('items-center justify-between ml-4 mb-4'):
            with ui.row().classes('items-center gap-2'):
                ui.icon('check_circle', color='green').style('font-size: 32px')
                ui.label("Active Contracts").classes("text-h5 font-bold")
            
            # Switch for Owned/Backup
            with ui.row().classes('items-center gap-2'):
                ui.label("Owned").classes("text-sm font-medium")
                owned_backup_switch = ui.switch(value=True, on_change=on_switch_toggle).props('color=primary')
                ui.label("Backup").classes("text-sm font-medium")
        
        ui.label("Contracts currently in effect").classes(
            "text-sm text-gray-500 ml-4 mb-4"
        )
        
        # Define search functions first
        def filter_contracts():
            search_term = (search_input.value or "").lower()
            if not search_term:
                contracts_table.rows = contract_rows
            else:
                filtered = [
                    row for row in contract_rows
                    if search_term in (row['contract_id'] or "").lower()
                    or search_term in (row['vendor_name'] or "").lower()
                    or search_term in (row['contract_type'] or "").lower()
                    or search_term in (row['description'] or "").lower()
                    or search_term in (row['manager'] or "").lower()
                ]
                contracts_table.rows = filtered
            contracts_table.update()
        
        def clear_search():
            search_input.value = ""
            contracts_table.rows = contract_rows
            contracts_table.update()
        
        # Search input for filtering contracts (above the table)
        with ui.row().classes('w-full ml-4 mr-4 mb-6 gap-2 px-2'):
            search_input = ui.input(placeholder='Search by Contract ID, Vendor, Type, Description, or Manager...').classes(
                'flex-1'
            ).props('outlined dense clearable')
            with search_input.add_slot('prepend'):
                ui.icon('search').classes('text-gray-400')
            search_button = ui.button(icon='search', on_click=filter_contracts).props('color=primary')
            clear_button = ui.button(icon='clear', on_click=clear_search).props('color=secondary')
        
        # Create table after search bar (showing all contracts)
        contracts_table = ui.table(
            columns=contract_columns,
            column_defaults=contract_columns_defaults,
            rows=contract_rows,
            pagination=10,
            row_key="contract_id"
        ).classes("w-full").props("flat bordered").classes(
            "contracts-table shadow-lg rounded-lg overflow-hidden"
        )
        
        search_input.on_value_change(filter_contracts)
        
        # Add custom CSS for visual highlighting
        ui.add_css("""
            .contracts-table thead tr {
                background-color: #144c8e !important;
            }
            .contracts-table tbody tr {
                background-color: white !important;
            }
        """)
        
        # Add slot for vendor name with clickable link
        contracts_table.add_slot('body-cell-vendor_name', '''
            <q-td :props="props">
                <a :href="'/vendor-info'" class="text-blue-600 hover:text-blue-800 underline cursor-pointer">
                    {{ props.value }}
                </a>
            </q-td>
        ''')
        
        # Add slot for status column with normal text
        contracts_table.add_slot('body-cell-status', '''
            <q-td :props="props">
                <div class="text-gray-700">
                    {{ props.value }}
                </div>
            </q-td>
        ''')
