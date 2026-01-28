from nicegui import ui
import io
import base64
from datetime import datetime
import os

from app.core.config import settings
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


def contract_managers():
    # Navigation
    with ui.row().classes("max-w-6xl mx-auto mt-4"):
        with ui.link(target='/').classes('no-underline'):
            ui.button("Back to Dashboard", icon="arrow_back").props('flat color=primary')
    
    # Global variables for table and data
    managers_table = None
    manager_rows = []
    
    # Fetch users with their active contract counts by role
    def fetch_users_with_contract_counts():
        """
        Fetches all users from the database and counts their active contracts
        in each role: Contract Manager, Backup, and Owner.
        """
        try:
            from app.db.database import SessionLocal
            from app.models.contract import User, Contract, ContractStatusType
            
            db = SessionLocal()
            try:
                # Get all active users
                users = db.query(User).filter(User.is_active == True).all()
                
                if not users:
                    print("No users found in database")
                    return []
                
                rows = []
                for user in users:
                    # Count active contracts where user is Contract Manager (contract_owner_id)
                    contract_manager_count = db.query(Contract).filter(
                        Contract.contract_owner_id == user.id,
                        Contract.status == ContractStatusType.ACTIVE
                    ).count()
                    
                    # Count active contracts where user is Backup (contract_owner_backup_id)
                    backup_count = db.query(Contract).filter(
                        Contract.contract_owner_backup_id == user.id,
                        Contract.status == ContractStatusType.ACTIVE
                    ).count()
                    
                    # Count active contracts where user is Owner (contract_owner_manager_id)
                    owner_count = db.query(Contract).filter(
                        Contract.contract_owner_manager_id == user.id,
                        Contract.status == ContractStatusType.ACTIVE
                    ).count()
                    
                    # Get department value
                    department = user.department.value if hasattr(user.department, 'value') else str(user.department)
                    
                    row_data = {
                        "user_id": str(user.user_id or ""),
                        "name": f"{user.first_name} {user.last_name}",
                        "email": str(user.email or ""),
                        "department": str(department or ""),
                        "contract_manager_count": int(contract_manager_count),
                        "backup_count": int(backup_count),
                        "owner_count": int(owner_count),
                    }
                    rows.append(row_data)
                
                print(f"Processed {len(rows)} user rows")
                return rows
                
            finally:
                db.close()
        except Exception as e:
            error_msg = f"Error fetching users: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            ui.notify(error_msg, type="negative")
            return []

    manager_columns = [
        {
            "name": "user_id",
            "label": "User ID",
            "field": "user_id",
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
            "name": "contract_manager_count",
            "label": "Contract Manager",
            "field": "contract_manager_count",
            "align": "center",
            "sortable": True,
        },
        {
            "name": "backup_count",
            "label": "Backup",
            "field": "backup_count",
            "align": "center",
            "sortable": True,
        },
        {
            "name": "owner_count",
            "label": "Owner",
            "field": "owner_count",
            "align": "center",
            "sortable": True,
        },
        {
            "name": "actions",
            "label": "",
            "field": "actions",
            "align": "center",
            "sortable": False,
        },
    ]

    manager_columns_defaults = {
        "align": "left",
        "headerClasses": "bg-[#144c8e] text-white",
    }

    manager_rows = fetch_users_with_contract_counts()
    
    # Main container
    with ui.element("div").classes("max-w-6xl mt-8 mx-auto w-full"):
        # Section header
        with ui.row().classes('items-center ml-4 mb-4 w-full justify-between'):
            with ui.row().classes('items-center gap-2'):
                ui.icon('people', color='primary').style('font-size: 32px')
                ui.label("User Administration").classes("text-h5 font-bold")
            # Create User button (entry point)
            ui.button(
                "Create User",
                icon="person_add",
                on_click=lambda: open_create_user_dialog(),
            ).props('color=primary').classes('mr-4')
        
        ui.label("View user responsibilities based on their assigned roles").classes(
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
                    if search_term in (row['user_id'] or "").lower()
                    or search_term in (row['name'] or "").lower()
                    or search_term in (row['email'] or "").lower()
                    or search_term in (row['department'] or "").lower()
                    or search_term in str(row.get('contract_manager_count', '')).lower()
                    or search_term in str(row.get('backup_count', '')).lower()
                    or search_term in str(row.get('owner_count', '')).lower()
                ]
                managers_table.rows = filtered
            managers_table.update()
        
        def clear_search():
            search_input.value = ""
            managers_table.rows = manager_rows
            managers_table.update()
        
        # Search input for filtering managers (above the table)
        with ui.row().classes('w-full ml-4 mr-4 mb-6 gap-2 px-2'):
            search_input = ui.input(placeholder='Search by ID, Name, Email, Department, or Contract Counts...').classes(
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
            row_key="user_id"
        ).classes("w-full").props("flat bordered").classes(
            "managers-table shadow-lg rounded-lg overflow-hidden"
        )
        
        search_input.on_value_change(filter_managers)
        
        # Generate button (moved from header to after table)
        ui.button("Generate", icon="description", on_click=lambda: open_generate_dialog()).props('color=primary').classes('ml-4 mt-4')
        
        # Add custom CSS for visual highlighting
        ui.add_css("""
            .managers-table thead tr {
                background-color: #144c8e !important;
            }
            .managers-table tbody tr {
                background-color: white !important;
            }
        """)
        
        # Add slot for contract manager count with centered badge
        managers_table.add_slot('body-cell-contract_manager_count', '''
            <q-td :props="props" class="text-center">
                <q-badge 
                    color="grey-6" 
                    :label="props.value"
                />
            </q-td>
        ''')
        
        # Add slot for backup count with centered badge
        managers_table.add_slot('body-cell-backup_count', '''
            <q-td :props="props" class="text-center">
                <q-badge 
                    color="grey-6" 
                    :label="props.value"
                />
            </q-td>
        ''')
        
        # Add slot for owner count with centered badge
        managers_table.add_slot('body-cell-owner_count', '''
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

        # Add actions column with pencil edit button
        managers_table.add_slot('body-cell-actions', '''
            <q-td :props="props" class="text-center">
                <q-btn 
                    flat round dense 
                    icon="edit" 
                    color="primary" 
                    @click="$parent.$emit('edit-user', props.row)"
                />
            </q-td>
        ''')

        def _extract_row_from_event(e):
            """Utility to extract row dict from NiceGUI/Quasar event arguments."""
            if not hasattr(e, 'args'):
                return None
            args = e.args
            if isinstance(args, list) and args:
                first = args[0]
                if isinstance(first, dict):
                    return first.get('row') or first
            if isinstance(args, dict):
                return args.get('row') or args
            return None

        # Handle pencil button click to edit user
        def handle_edit_button(e):
            """Open edit dialog when the pencil icon is clicked."""
            row = _extract_row_from_event(e)
            if not row:
                # pending_reviews uses the row dict directly in e.args; support that too
                row = e.args if hasattr(e, "args") else None
            if isinstance(row, dict):
                open_edit_user_dialog(row)

        managers_table.on('edit-user', handle_edit_button)
        
        # Function to open Create User dialog
        def open_create_user_dialog():
            """Open dialog to create a new user"""
            from app.db.database import SessionLocal
            from app.models.contract import User, DepartmentType, UserRole
            from app.services.contract_service import ContractService

            with ui.dialog() as dialog, ui.card().classes('p-6 w-full max-w-lg'):
                ui.label("Create User").classes("text-h6 font-bold mb-2")
                ui.label(
                    "Add a new user to the system. All fields are required."
                ).classes("text-sm text-gray-600 mb-4")

                label_classes = "text-sm font-semibold text-gray-700"
                input_classes = "w-full"

                with ui.column().classes('gap-3 w-full'):
                    # First Name
                    ui.label("First Name*").classes(label_classes)
                    first_name_input = ui.input().classes(input_classes).props("outlined")
                    first_name_error = ui.label('').classes(
                        'text-red-600 text-xs min-h-[18px]'
                    ).style('display:none')

                    # Last Name
                    ui.label("Last Name*").classes(label_classes + " mt-1")
                    last_name_input = ui.input().classes(input_classes).props("outlined")
                    last_name_error = ui.label('').classes(
                        'text-red-600 text-xs min-h-[18px]'
                    ).style('display:none')

                    # Email
                    ui.label("Email*").classes(label_classes + " mt-1")
                    email_input = ui.input().classes(input_classes).props(
                        "outlined type=email"
                    )
                    email_error = ui.label('').classes(
                        'text-red-600 text-xs min-h-[18px]'
                    ).style('display:none')

                    # Department
                    ui.label("Department*").classes(label_classes + " mt-1")
                    try:
                        from app.models.contract import DepartmentType

                        department_options = [d.value for d in DepartmentType]
                    except Exception:
                        department_options = []
                    department_select = ui.select(
                        options=department_options,
                        label="Select department",
                    ).classes(input_classes).props("outlined")
                    department_error = ui.label('').classes(
                        'text-red-600 text-xs min-h-[18px]'
                    ).style('display:none')

                    # Phone (captured for administration, not yet stored in DB)
                    ui.label("Phone*").classes(label_classes + " mt-1")
                    phone_input = ui.input().classes(input_classes).props("outlined")
                    phone_error = ui.label('').classes(
                        'text-red-600 text-xs min-h-[18px]'
                    ).style('display:none')

                    # Access Role
                    ui.label("Access Role*").classes(label_classes + " mt-1")
                    try:
                        from app.models.contract import UserRole

                        role_options = [r.value for r in UserRole]
                    except Exception:
                        role_options = []
                    role_select = ui.select(
                        options=role_options,
                        label="Select access role",
                    ).classes(input_classes).props("outlined")
                    role_error = ui.label('').classes(
                        'text-red-600 text-xs min-h-[18px]'
                    ).style('display:none')

                    # Helper to mark invalid fields
                    def mark_invalid(input_control, error_label, message: str):
                        error_label.text = message
                        error_label.style('display:block')
                        input_control.classes('border border-red-600')

                    def clear_error(input_control, error_label):
                        error_label.text = ''
                        error_label.style('display:none')
                        input_control.classes(remove='border border-red-600')

                    # Create and Cancel buttons
                    with ui.row().classes('justify-end gap-2 mt-4 w-full'):
                        ui.button("Cancel", on_click=dialog.close).props('flat')

                        def create_user():
                            """Validate form and create user in database"""
                            # Basic validations
                            valid = True

                            first_name = (first_name_input.value or '').strip()
                            if not first_name:
                                mark_invalid(
                                    first_name_input,
                                    first_name_error,
                                    "First name is required",
                                )
                                valid = False
                            else:
                                clear_error(first_name_input, first_name_error)

                            last_name = (last_name_input.value or '').strip()
                            if not last_name:
                                mark_invalid(
                                    last_name_input,
                                    last_name_error,
                                    "Last name is required",
                                )
                                valid = False
                            else:
                                clear_error(last_name_input, last_name_error)

                            email = (email_input.value or '').strip()
                            if not email:
                                mark_invalid(
                                    email_input,
                                    email_error,
                                    "Email is required",
                                )
                                valid = False
                            elif '@' not in email or '.' not in email:
                                mark_invalid(
                                    email_input,
                                    email_error,
                                    "Please enter a valid email address",
                                )
                                valid = False
                            else:
                                clear_error(email_input, email_error)

                            department_val = department_select.value or ''
                            if not department_val:
                                mark_invalid(
                                    department_select,
                                    department_error,
                                    "Department is required",
                                )
                                valid = False
                            else:
                                clear_error(department_select, department_error)

                            phone = (phone_input.value or '').strip()
                            if not phone:
                                mark_invalid(
                                    phone_input,
                                    phone_error,
                                    "Phone is required",
                                )
                                valid = False
                            else:
                                clear_error(phone_input, phone_error)

                            role_val = role_select.value or ''
                            if not role_val:
                                mark_invalid(
                                    role_select,
                                    role_error,
                                    "Access role is required",
                                )
                                valid = False
                            else:
                                clear_error(role_select, role_error)

                            if not valid:
                                ui.notify(
                                    "Please complete all required fields.",
                                    type="negative",
                                )
                                return

                            # Create user in database
                            try:
                                db = SessionLocal()
                                try:
                                    contract_service = ContractService(db)
                                    generated_user_id = contract_service.generate_user_id()

                                    try:
                                        department_enum = DepartmentType(department_val)
                                    except ValueError:
                                        mark_invalid(
                                            department_select,
                                            department_error,
                                            "Invalid department selected",
                                        )
                                        ui.notify(
                                            "Invalid department selected.",
                                            type="negative",
                                        )
                                        return

                                    try:
                                        role_enum = UserRole(role_val)
                                    except ValueError:
                                        mark_invalid(
                                            role_select,
                                            role_error,
                                            "Invalid role selected",
                                        )
                                        ui.notify(
                                            "Invalid access role selected.",
                                            type="negative",
                                        )
                                        return

                                    new_user = User(
                                        user_id=generated_user_id,
                                        first_name=first_name,
                                        last_name=last_name,
                                        email=email,
                                        department=department_enum,
                                        position="Employee",
                                        role=role_enum,
                                        is_active=True,
                                        hashed_password=None,
                                    )

                                    db.add(new_user)
                                    db.commit()
                                    db.refresh(new_user)

                                    # Add to table data with zero contract counts
                                    row_data = {
                                        "user_id": str(new_user.user_id or ""),
                                        "name": f"{new_user.first_name} {new_user.last_name}",
                                        "email": str(new_user.email or ""),
                                        "department": str(
                                            new_user.department.value
                                            if hasattr(new_user.department, 'value')
                                            else new_user.department
                                        ),
                                        "contract_manager_count": 0,
                                        "backup_count": 0,
                                        "owner_count": 0,
                                    }
                                    manager_rows.append(row_data)
                                    managers_table.rows = manager_rows
                                    managers_table.update()

                                    ui.notify(
                                        f"User {new_user.first_name} {new_user.last_name} created successfully.",
                                        type="positive",
                                    )
                                    dialog.close()
                                finally:
                                    db.close()
                            except Exception as e:
                                ui.notify(
                                    f"Error creating user: {str(e)}", type="negative"
                                )

                        ui.button(
                            "Create",
                            icon="check",
                            on_click=create_user,
                        ).props('color=primary')

                dialog.open()

        # Function to open Edit User dialog
        def open_edit_user_dialog(row_data: dict):
            """Open dialog to edit an existing user."""
            from app.db.database import SessionLocal
            from app.models.contract import User, DepartmentType, UserRole

            current_user_id = row_data.get('user_id', '')

            # Fetch the latest user data from DB when opening the modal
            try:
                db_preview = SessionLocal()
                try:
                    user_preview = (
                        db_preview.query(User)
                        .filter(User.user_id == current_user_id)
                        .first()
                    )
                    if not user_preview:
                        ui.notify("User not found in database.", type="negative")
                        return

                    current_first_name = str(user_preview.first_name or "")
                    current_last_name = str(user_preview.last_name or "")
                    current_email = str(user_preview.email or "")
                    current_department = (
                        user_preview.department.value
                        if getattr(user_preview.department, "value", None) is not None
                        else str(user_preview.department or "")
                    )
                    current_role_value = (
                        user_preview.role.value
                        if getattr(user_preview.role, "value", None) is not None
                        else (str(user_preview.role) if user_preview.role else None)
                    )
                finally:
                    db_preview.close()
            except Exception as e:
                ui.notify(f"Error loading user data: {str(e)}", type="negative")
                return

            with ui.dialog() as dialog, ui.card().classes('p-6 w-full max-w-lg'):
                ui.label("Edit User").classes("text-h6 font-bold mb-2")
                ui.label(
                    "Modify user information. All fields are required."
                ).classes("text-sm text-gray-600 mb-4")

                label_classes = "text-sm font-semibold text-gray-700"
                input_classes = "w-full"

                with ui.column().classes('gap-3 w-full'):
                    # First Name
                    ui.label("First Name*").classes(label_classes)
                    first_name_input = ui.input(
                        value=current_first_name,
                    ).classes(input_classes).props("outlined")
                    first_name_error = ui.label('').classes(
                        'text-red-600 text-xs min-h-[18px]'
                    ).style('display:none')

                    # Last Name
                    ui.label("Last Name*").classes(label_classes + " mt-1")
                    last_name_input = ui.input(
                        value=current_last_name,
                    ).classes(input_classes).props("outlined")
                    last_name_error = ui.label('').classes(
                        'text-red-600 text-xs min-h-[18px]'
                    ).style('display:none')

                    # Email
                    ui.label("Email*").classes(label_classes + " mt-1")
                    email_input = ui.input(
                        value=current_email,
                    ).classes(input_classes).props("outlined type=email")
                    email_error = ui.label('').classes(
                        'text-red-600 text-xs min-h-[18px]'
                    ).style('display:none')

                    # Department
                    ui.label("Department*").classes(label_classes + " mt-1")
                    try:
                        department_options = [d.value for d in DepartmentType]
                    except Exception:
                        department_options = []
                    department_select = ui.select(
                        options=department_options,
                        value=current_department if current_department in department_options else None,
                        label="Select department",
                    ).classes(input_classes).props("outlined")
                    department_error = ui.label('').classes(
                        'text-red-600 text-xs min-h-[18px]'
                    ).style('display:none')

                    # Phone (UI only, not yet stored in DB)
                    ui.label("Phone*").classes(label_classes + " mt-1")
                    phone_input = ui.input().classes(input_classes).props("outlined")
                    phone_error = ui.label('').classes(
                        'text-red-600 text-xs min-h-[18px]'
                    ).style('display:none')

                    # Access Role
                    ui.label("Access Role*").classes(label_classes + " mt-1")
                    try:
                        role_options = [r.value for r in UserRole]
                    except Exception:
                        role_options = []

                    role_select = ui.select(
                        options=role_options,
                        value=current_role_value if current_role_value in role_options else None,
                        label="Select access role",
                    ).classes(input_classes).props("outlined")
                    role_error = ui.label('').classes(
                        'text-red-600 text-xs min-h-[18px]'
                    ).style('display:none')

                    # Helpers
                    def mark_invalid(input_control, error_label, message: str):
                        error_label.text = message
                        error_label.style('display:block')
                        input_control.classes('border border-red-600')

                    def clear_error(input_control, error_label):
                        error_label.text = ''
                        error_label.style('display:none')
                        input_control.classes(remove='border border-red-600')

                    # Buttons
                    with ui.row().classes('justify-end gap-2 mt-4 w-full'):
                        ui.button("Cancel", on_click=dialog.close).props('flat')

                        def modify_user():
                            """Validate and update user information in the database."""
                            valid = True

                            first_name = (first_name_input.value or '').strip()
                            if not first_name:
                                mark_invalid(
                                    first_name_input,
                                    first_name_error,
                                    "First name is required",
                                )
                                valid = False
                            else:
                                clear_error(first_name_input, first_name_error)

                            last_name = (last_name_input.value or '').strip()
                            if not last_name:
                                mark_invalid(
                                    last_name_input,
                                    last_name_error,
                                    "Last name is required",
                                )
                                valid = False
                            else:
                                clear_error(last_name_input, last_name_error)

                            email = (email_input.value or '').strip()
                            if not email:
                                mark_invalid(
                                    email_input,
                                    email_error,
                                    "Email is required",
                                )
                                valid = False
                            elif '@' not in email or '.' not in email:
                                mark_invalid(
                                    email_input,
                                    email_error,
                                    "Please enter a valid email address",
                                )
                                valid = False
                            else:
                                clear_error(email_input, email_error)

                            department_val = department_select.value or ''
                            if not department_val:
                                mark_invalid(
                                    department_select,
                                    department_error,
                                    "Department is required",
                                )
                                valid = False
                            else:
                                clear_error(department_select, department_error)

                            phone = (phone_input.value or '').strip()
                            if not phone:
                                mark_invalid(
                                    phone_input,
                                    phone_error,
                                    "Phone is required",
                                )
                                valid = False
                            else:
                                clear_error(phone_input, phone_error)

                            role_val = role_select.value or ''
                            if not role_val:
                                mark_invalid(
                                    role_select,
                                    role_error,
                                    "Access role is required",
                                )
                                valid = False
                            else:
                                clear_error(role_select, role_error)

                            if not valid:
                                ui.notify(
                                    "Please complete all required fields.",
                                    type="negative",
                                )
                                return

                            # Update in database
                            try:
                                db = SessionLocal()
                                try:
                                    user = (
                                        db.query(User)
                                        .filter(User.user_id == current_user_id)
                                        .first()
                                    )
                                    if not user:
                                        ui.notify(
                                            "User not found in database.",
                                            type="negative",
                                        )
                                        return

                                    try:
                                        department_enum = DepartmentType(
                                            department_val
                                        )
                                    except ValueError:
                                        mark_invalid(
                                            department_select,
                                            department_error,
                                            "Invalid department selected",
                                        )
                                        ui.notify(
                                            "Invalid department selected.",
                                            type="negative",
                                        )
                                        return

                                    try:
                                        role_enum = UserRole(role_val)
                                    except ValueError:
                                        mark_invalid(
                                            role_select,
                                            role_error,
                                            "Invalid role selected",
                                        )
                                        ui.notify(
                                            "Invalid access role selected.",
                                            type="negative",
                                        )
                                        return

                                    # Apply changes
                                    user.first_name = first_name
                                    user.last_name = last_name
                                    user.email = email
                                    user.department = department_enum
                                    user.role = role_enum

                                    db.commit()
                                    db.refresh(user)

                                    # Update row data in table
                                    row_data['user_id'] = str(user.user_id or "")
                                    row_data['name'] = f"{user.first_name} {user.last_name}"
                                    row_data['email'] = str(user.email or "")
                                    row_data['department'] = str(
                                        user.department.value
                                        if hasattr(user.department, 'value')
                                        else user.department
                                    )

                                    managers_table.update()

                                    ui.notify(
                                        f"User {user.first_name} {user.last_name} updated successfully.",
                                        type="positive",
                                    )
                                    dialog.close()
                                finally:
                                    db.close()
                            except Exception as e:
                                ui.notify(
                                    f"Error updating user: {str(e)}", type="negative"
                                )

                        ui.button(
                            "Modify",
                            icon="check",
                            on_click=modify_user,
                        ).props('color=primary')

                dialog.open()

        # Function to generate Excel report
        def open_generate_dialog():
            """Open dialog for report generation"""
            with ui.dialog() as dialog, ui.card().classes('p-6 w-full max-w-md'):
                ui.label("Generate User Administration Report").classes("text-h6 font-bold mb-4")
                
                with ui.column().classes('gap-4 w-full'):
                    ui.label("This report will include all users with their contract responsibilities.").classes("text-sm text-gray-600")
                    
                    ui.label("The report will include: User ID, Name, Email, Department, Contract Manager count, Backup count, and Owner count.").classes("text-xs text-gray-500 italic")
                    
                    with ui.row().classes('gap-2 justify-end w-full mt-4'):
                        ui.button("Cancel", on_click=dialog.close).props('flat')
                        ui.button("Generate & Download", icon="download", 
                                 on_click=lambda: generate_excel_report(dialog)).props('color=primary')
                
                dialog.open()
        
        def generate_excel_report(dialog):
            """Generate Excel report for user administration"""
            try:
                if not PANDAS_AVAILABLE:
                    ui.notify("Excel export requires pandas library. Please install it: pip install pandas openpyxl", type="negative")
                    dialog.close()
                    return
                
                if not manager_rows:
                    ui.notify("No users available for export", type="warning")
                    dialog.close()
                    return
                
                # Prepare data for Excel
                report_data = []
                for user in manager_rows:
                    report_data.append({
                        "User ID": user.get('user_id', ''),
                        "Name": user.get('name', ''),
                        "Email": user.get('email', ''),
                        "Department": user.get('department', ''),
                        "Contract Manager": user.get('contract_manager_count', 0),
                        "Backup": user.get('backup_count', 0),
                        "Owner": user.get('owner_count', 0),
                    })
                
                # Create DataFrame
                df = pd.DataFrame(report_data)
                
                # Create Excel file in memory
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='User Administration')
                    
                    # Get the worksheet
                    worksheet = writer.sheets['User Administration']
                    
                    # Auto-adjust column widths
                    for column in worksheet.columns:
                        max_length = 0
                        column_letter = column[0].column_letter
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except (AttributeError, TypeError):
                                pass
                        adjusted_width = min(max_length + 2, 50)
                        worksheet.column_dimensions[column_letter].width = adjusted_width
                
                output.seek(0)
                
                # Convert to base64 for download
                excel_data = output.getvalue()
                b64_data = base64.b64encode(excel_data).decode()
                
                # Generate filename
                today = datetime.now().strftime("%Y-%m-%d")
                filename = f"User_Administration_Report_{today}.xlsx"
                
                # Trigger download using JavaScript
                ui.run_javascript(f'''
                    const link = document.createElement('a');
                    link.href = 'data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64_data}';
                    link.download = '{filename}';
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                ''')
                
                ui.notify(f"Report generated successfully! {len(manager_rows)} user(s) exported.", type="positive")
                dialog.close()
                
            except Exception as e:
                ui.notify(f"Error generating report: {str(e)}", type="negative")
                import traceback
                traceback.print_exc()
