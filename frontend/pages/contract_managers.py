from nicegui import ui


def contract_managers():
    # Navigation
    with ui.row().classes("max-w-6xl mx-auto mt-4"):
        with ui.link(target='/').classes('no-underline'):
            ui.button("Back to Dashboard", icon="arrow_back").props('flat color=primary')
    
    # Global variables for table and data
    managers_table = None
    manager_rows = []
    
    # Mock data for contract managers
    def get_mock_managers():
        """
        Simulates contract managers data.
        This will be replaced with actual API call when available.
        """
        
        mock_managers = [
            {
                "manager_id": "MGR-001",
                "name": "William Defoe",
                "email": "william.defoe@company.com",
                "department": "IT Operations",
                "role": "Owner",
                "active_contracts": 12,
                "phone": "+297 582 1234"
            },
            {
                "manager_id": "MGR-002",
                "name": "John Doe",
                "email": "john.doe@company.com",
                "department": "Finance",
                "role": "Backup",
                "active_contracts": 8,
                "phone": "+297 582 1235"
            },
            {
                "manager_id": "MGR-003",
                "name": "Sarah Mitchell",
                "email": "sarah.mitchell@company.com",
                "department": "Human Resources",
                "role": "Owner",
                "active_contracts": 15,
                "phone": "+297 582 1236"
            },
            {
                "manager_id": "MGR-004",
                "name": "Michael Chen",
                "email": "michael.chen@company.com",
                "department": "Compliance",
                "role": "Owner",
                "active_contracts": 10,
                "phone": "+297 582 1237"
            },
            {
                "manager_id": "MGR-005",
                "name": "Emily Rodriguez",
                "email": "emily.rodriguez@company.com",
                "department": "Marketing",
                "role": "Backup",
                "active_contracts": 6,
                "phone": "+297 582 1238"
            },
            {
                "manager_id": "MGR-006",
                "name": "David Thompson",
                "email": "david.thompson@company.com",
                "department": "Security",
                "role": "Owner",
                "active_contracts": 18,
                "phone": "+297 582 1239"
            },
            {
                "manager_id": "MGR-007",
                "name": "Jessica Park",
                "email": "jessica.park@company.com",
                "department": "Premises & Facilities",
                "role": "Backup",
                "active_contracts": 9,
                "phone": "+297 582 1240"
            },
            {
                "manager_id": "MGR-008",
                "name": "Robert Williams",
                "email": "robert.williams@company.com",
                "department": "Internal Audit",
                "role": "Owner",
                "active_contracts": 7,
                "phone": "+297 582 1241"
            },
            {
                "manager_id": "MGR-009",
                "name": "Amanda Garcia",
                "email": "amanda.garcia@company.com",
                "department": "Payment Operations",
                "role": "Owner",
                "active_contracts": 14,
                "phone": "+297 582 1242"
            },
            {
                "manager_id": "MGR-010",
                "name": "Christopher Lee",
                "email": "christopher.lee@company.com",
                "department": "Corporate Banking",
                "role": "Backup",
                "active_contracts": 11,
                "phone": "+297 582 1243"
            },
            {
                "manager_id": "MGR-011",
                "name": "Maria Santos",
                "email": "maria.santos@company.com",
                "department": "Retail Banking",
                "role": "Owner",
                "active_contracts": 13,
                "phone": "+297 582 1244"
            },
            {
                "manager_id": "MGR-012",
                "name": "James Anderson",
                "email": "james.anderson@company.com",
                "department": "Credit Risk",
                "role": "Backup",
                "active_contracts": 5,
                "phone": "+297 582 1245"
            },
            {
                "manager_id": "MGR-013",
                "name": "Linda Peterson",
                "email": "linda.peterson@company.com",
                "department": "Executive Office",
                "role": "Owner",
                "active_contracts": 16,
                "phone": "+297 582 1246"
            },
            {
                "manager_id": "MGR-014",
                "name": "Daniel Martinez",
                "email": "daniel.martinez@company.com",
                "department": "IT Projects",
                "role": "Backup",
                "active_contracts": 10,
                "phone": "+297 582 1247"
            },
            {
                "manager_id": "MGR-015",
                "name": "Patricia Brown",
                "email": "patricia.brown@company.com",
                "department": "Business Continuity",
                "role": "Owner",
                "active_contracts": 9,
                "phone": "+297 582 1248"
            },
        ]
        
        return mock_managers

    manager_columns = [
        {
            "name": "manager_id",
            "label": "Manager ID",
            "field": "manager_id",
            "align": "left",
            "sortable": True,
        },
        {
            "name": "name",
            "label": "Name",
            "field": "name",
            "align": "left",
            "sortable": True,
        },
        {
            "name": "email",
            "label": "Email",
            "field": "email",
            "align": "left",
            "sortable": True,
        },
        {
            "name": "department",
            "label": "Department",
            "field": "department",
            "align": "left",
            "sortable": True,
        },
        {
            "name": "phone",
            "label": "Phone",
            "field": "phone",
            "align": "left",
        },
        {
            "name": "role",
            "label": "Role",
            "field": "role",
            "align": "left",
            "sortable": True,
        },
        {
            "name": "active_contracts",
            "label": "Active Contracts",
            "field": "active_contracts",
            "align": "center",
            "sortable": True,
        },
    ]

    manager_columns_defaults = {
        "align": "left",
        "headerClasses": "bg-[#144c8e] text-white",
    }

    manager_rows = get_mock_managers()
    
    # Main container
    with ui.element("div").classes("max-w-6xl mt-8 mx-auto w-full"):
        # Section header
        with ui.row().classes('items-center justify-between ml-4 mb-4'):
            with ui.row().classes('items-center gap-2'):
                ui.icon('people', color='primary').style('font-size: 32px')
                ui.label("Contract Managers").classes("text-h5 font-bold")
        
        ui.label("Manage contract owners and backup managers").classes(
            "text-sm text-gray-500 ml-4 mb-4"
        )
        
        # Define search functions first
        def filter_managers():
            search_term = (search_input.value or "").lower()
            if not search_term:
                managers_table.rows = manager_rows
            else:
                filtered = [
                    row for row in manager_rows
                    if search_term in (row['manager_id'] or "").lower()
                    or search_term in (row['name'] or "").lower()
                    or search_term in (row['email'] or "").lower()
                    or search_term in (row['department'] or "").lower()
                    or search_term in (row['role'] or "").lower()
                ]
                managers_table.rows = filtered
            managers_table.update()
        
        def clear_search():
            search_input.value = ""
            managers_table.rows = manager_rows
            managers_table.update()
        
        # Search input for filtering managers (above the table)
        with ui.row().classes('w-full ml-4 mr-4 mb-6 gap-2 px-2'):
            search_input = ui.input(placeholder='Search by ID, Name, Email, Department, or Role...').classes(
                'flex-1'
            ).props('outlined dense clearable')
            with search_input.add_slot('prepend'):
                ui.icon('search').classes('text-gray-400')
            search_button = ui.button(icon='search', on_click=filter_managers).props('color=primary')
            clear_button = ui.button(icon='clear', on_click=clear_search).props('color=secondary')
        
        # Create table after search bar
        managers_table = ui.table(
            columns=manager_columns,
            column_defaults=manager_columns_defaults,
            rows=manager_rows,
            pagination=10,
            row_key="manager_id"
        ).classes("w-full").props("flat bordered").classes(
            "managers-table shadow-lg rounded-lg overflow-hidden"
        )
        
        search_input.on_value_change(filter_managers)
        
        # Add custom CSS for visual highlighting
        ui.add_css("""
            .managers-table thead tr {
                background-color: #144c8e !important;
            }
            .managers-table tbody tr {
                background-color: white !important;
            }
        """)
        
        # Add slot for role column with badge styling
        managers_table.add_slot('body-cell-role', '''
            <q-td :props="props">
                <q-badge 
                    :color="props.value === 'Owner' ? 'primary' : 'orange'" 
                    :label="props.value"
                />
            </q-td>
        ''')
        
        # Add slot for active contracts with centered badge
        managers_table.add_slot('body-cell-active_contracts', '''
            <q-td :props="props" class="text-center">
                <q-badge 
                    color="grey-6" 
                    :label="props.value"
                />
            </q-td>
        ''')
        
        # Add slot for email with mailto link
        managers_table.add_slot('body-cell-email', '''
            <q-td :props="props">
                <a :href="'mailto:' + props.value" class="text-blue-600 hover:text-blue-800 underline">
                    {{ props.value }}
                </a>
            </q-td>
        ''')




