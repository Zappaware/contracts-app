
import requests
from nicegui import ui


def vendors_list():
    # Navigation
    with ui.row().classes("max-w-6xl mx-auto mt-4 items-center gap-4"):
        with ui.link(target='/').classes('no-underline'):
            ui.button("Back to Dashboard", icon="arrow_back").props('flat color=primary')
    
    # Fetch vendors from API
    def fetch_vendors():
        """
        Fetches vendors from the backend API.
        """
        base_url = "http://localhost:8000/api/v1"
        url = f"{base_url}/vendors/?limit=1000"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Debug: Show what we received
            print(f"API Response: {data}")
            
            # The API returns: {"vendors": [...], "total_count": ..., ...}
            vendors = data.get("vendors", [])
            
            print(f"Found {len(vendors)} vendors in API response")
            
            if not vendors:
                ui.notify("No vendors found in API response", type="warning")
                print(f"Vendors list is empty. Full response keys: {list(data.keys())}")
                print(f"Full response: {data}")
                return []
            
            # Map backend vendor data to table row format
            rows = []
            for v in vendors:
                # Format next_required_due_diligence_date
                next_dd_date = v.get("next_required_due_diligence_date")
                if next_dd_date:
                    # Handle ISO format date string
                    if isinstance(next_dd_date, str):
                        try:
                            from datetime import datetime
                            date_obj = datetime.fromisoformat(next_dd_date.replace('Z', '+00:00'))
                            formatted_date = date_obj.strftime("%Y-%m-%d")
                        except:
                            formatted_date = next_dd_date.split('T')[0] if 'T' in next_dd_date else next_dd_date
                    else:
                        formatted_date = str(next_dd_date)
                else:
                    formatted_date = "N/A"
                
                # Determine attention/status indicator
                status = v.get("status", "Unknown")
                status_color = v.get("status_color", "gray")
                is_overdue = v.get("is_due_diligence_overdue", False)
                
                attention = ""
                if is_overdue:
                    attention = "⚠️ Due Diligence Overdue"
                elif status == "Active":
                    attention = "✓ Active"
                else:
                    attention = "○ Inactive"
                
                # Get ID - must be integer for row_key
                vendor_id = v.get("id")
                if vendor_id is None:
                    continue  # Skip rows without ID
                
                row_data = {
                    "id": int(vendor_id),  # Must be integer for row_key
                    "vendor_id": str(v.get("vendor_id") or ""),
                    "vendor_name": str(v.get("vendor_name") or ""),
                    "contact": str(v.get("vendor_contact_person") or ""),
                    "email": str(v.get("email") or ""),
                    "next_dd_date": str(formatted_date),
                    "status": str(status or "Unknown"),
                    "status_color": str(status_color or "gray"),
                    "attention": str(attention),
                    "is_overdue": bool(is_overdue or False),
                }
                rows.append(row_data)
            
            print(f"Processed {len(rows)} vendor rows")
            return rows
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Error fetching vendors: {str(e)}"
            print(error_msg)
            ui.notify(error_msg, type="negative")
            return []
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            ui.notify(error_msg, type="negative")
            return []
    
    # Define table columns
    vendor_columns = [
        {
            "name": "vendor_id",
            "label": "Vendor ID",
            "field": "vendor_id",
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
            "name": "contact",
            "label": "Contact Person",
            "field": "contact",
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
            "name": "next_dd_date",
            "label": "Next Due Diligence Date",
            "field": "next_dd_date",
            "align": "left",
            "sortable": True,
        },
        {
            "name": "status",
            "label": "Status",
            "field": "status",
            "align": "left",
            "sortable": True,
        },
        {
            "name": "attention",
            "label": "Attention",
            "field": "attention",
            "align": "left",
        },
    ]
    
    vendor_columns_defaults = {
        "align": "left",
        "headerClasses": "bg-[#144c8e] text-white",
    }
    
    # Fetch vendors data - use global to allow refresh
    vendor_rows = []
    
    # Initial fetch
    vendor_rows = fetch_vendors()
    
    # Debug: Check if we have data
    print(f"Total vendor rows fetched: {len(vendor_rows)}")
    if vendor_rows:
        print(f"First row sample: {vendor_rows[0]}")
    else:
        ui.notify("No vendor data available. Please check the API connection.", type="warning")
    
    # Page header
    with ui.element("div").classes("max-w-6xl mx-auto mt-8 w-full"):
        with ui.row().classes('items-center justify-between ml-4 mb-4 w-full'):
            ui.label("Vendor List").classes("text-h5 font-bold")
            count_label = ui.label(f"Total: {len(vendor_rows)} vendors").classes("text-sm text-gray-500")
        
        # Search functionality (defined before table so it can reference vendors_table)
        def filter_vendors():
            if not vendors_table:
                return
            search_term = (search_input.value or "").lower()
            if not search_term:
                vendors_table.rows = vendor_rows
            else:
                filtered = [
                    row for row in vendor_rows
                    if search_term in (row.get("vendor_id") or "").lower()
                    or search_term in (row.get("vendor_name") or "").lower()
                    or search_term in (row.get("contact") or "").lower()
                    or search_term in (row.get("email") or "").lower()
                ]
                vendors_table.rows = filtered
            vendors_table.update()
        
        def clear_search():
            search_input.value = ""
            filter_vendors()
        
        # Search input
        with ui.row().classes('w-full ml-4 mr-4 mb-6 gap-2 px-2'):
            search_input = ui.input(placeholder='Search by Vendor ID, Name, Contact, or Email...').classes(
                'flex-1'
            ).props('outlined dense clearable')
            with search_input.add_slot('prepend'):
                ui.icon('search').classes('text-gray-400')
            ui.button(icon='search', on_click=filter_vendors).props('color=primary')
            ui.button(icon='clear', on_click=clear_search).props('color=secondary')
        
        # Show message if no data
        if not vendor_rows:
            with ui.card().classes("w-full p-6"):
                ui.label("No vendors found").classes("text-lg font-bold text-gray-500")
                ui.label("Please check that the backend API is running and has vendor data.").classes("text-sm text-gray-400 mt-2")
        
        # Vendors table - ensure it's created with data
        table_rows = vendor_rows if vendor_rows else []
        print(f"Creating table with {len(table_rows)} rows")
        
        vendors_table = ui.table(
            columns=vendor_columns,
            column_defaults=vendor_columns_defaults,
            rows=table_rows,
            pagination=10,
            row_key="id"
        ).classes("w-full").props("flat bordered").classes(
            "vendors-table shadow-lg rounded-lg overflow-hidden"
        )
        
        # Force update if we have data
        if table_rows:
            vendors_table.update()
        
        # Refresh function (defined after table is created)
        def refresh_vendors():
            nonlocal vendor_rows
            vendor_rows = fetch_vendors()
            vendors_table.rows = vendor_rows if vendor_rows else []
            vendors_table.update()
            count_label.set_text(f"Total: {len(vendor_rows)} vendors")
            ui.notify(f"Refreshed: {len(vendor_rows)} vendors loaded", type="info")
        
        # Add refresh button to header
        refresh_btn = ui.button("Refresh", icon="refresh", on_click=refresh_vendors).props('color=primary flat').classes('ml-4')
        
        search_input.on_value_change(filter_vendors)
        
        # Add custom CSS
        ui.add_css("""
            .vendors-table thead tr {
                background-color: #144c8e !important;
            }
            .vendors-table tbody tr:has(td:contains("Overdue")) {
                background-color: #fee2e2 !important;
            }
        """)
        
        # Add slot for vendor name with clickable link
        vendors_table.add_slot('body-cell-vendor_name', '''
            <q-td :props="props">
                <a :href="'/vendor-info'" class="text-blue-600 hover:text-blue-800 underline cursor-pointer">
                    {{ props.value }}
                </a>
            </q-td>
        ''')
        
        # Add slot for status column with color coding
        vendors_table.add_slot('body-cell-status', '''
            <q-td :props="props">
                <div v-if="props.row.status_color === 'green'" class="text-green-700 font-semibold">
                    {{ props.value }}
                </div>
                <div v-else class="text-gray-700 font-semibold">
                    {{ props.value }}
                </div>
            </q-td>
        ''')
        
        # Add slot for attention column with styling
        vendors_table.add_slot('body-cell-attention', '''
            <q-td :props="props">
                <div v-if="props.value.includes('Overdue')" class="text-red-700 font-bold flex items-center gap-1">
                    <q-icon name="error" color="red" size="sm" />
                    {{ props.value }}
                </div>
                <div v-else-if="props.value.includes('Active')" class="text-green-700 font-semibold flex items-center gap-1">
                    <q-icon name="check_circle" color="green" size="sm" />
                    {{ props.value }}
                </div>
                <div v-else class="text-gray-600 font-semibold">
                    {{ props.value }}
                </div>
            </q-td>
        ''')

