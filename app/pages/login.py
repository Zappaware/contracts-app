from nicegui import app, ui
from app.db.database import SessionLocal
from app.models.contract import User, UserRole

def login_page():
    username_input = None
    password_input = None
    
    def do_login():
        if not username_input or not username_input.value:
            ui.notify("Please enter a username", type="negative")
            return
        
        username = username_input.value
        password = password_input.value if password_input else ""
        
        # Look up user in database
        db = SessionLocal()
        try:
            # Try multiple matching strategies
            current_user = db.query(User).filter(User.email == username).first()
            if not current_user:
                current_user = db.query(User).filter(User.email.ilike(f"%{username}%")).first()
            if not current_user:
                current_user = db.query(User).filter(User.first_name.ilike(f"%{username}%")).first()
            if not current_user:
                current_user = db.query(User).filter(User.last_name.ilike(f"%{username}%")).first()
            if not current_user and ' ' in username:
                parts = username.split()
                if len(parts) >= 2:
                    current_user = db.query(User).filter(
                        User.first_name.ilike(f"%{parts[0]}%"),
                        User.last_name.ilike(f"%{parts[-1]}%")
                    ).first()
            
            if not current_user:
                ui.notify("User not found. Please check your username.", type="negative")
                return
            
            # Store user info
            app.storage.user['logged_in'] = True
            app.storage.user['username'] = current_user.email
            app.storage.user['user_id'] = current_user.id
            app.storage.user['user_role'] = current_user.role.value if current_user.role else None
            
            # Navigate based on role
            if current_user.role == UserRole.CONTRACT_ADMIN:
                ui.navigate.to('/')
            elif current_user.role in [UserRole.CONTRACT_MANAGER, UserRole.CONTRACT_MANAGER_BACKUP, UserRole.CONTRACT_MANAGER_OWNER]:
                ui.navigate.to('/manager')
            else:
                # Default to manager page for unknown roles
                ui.navigate.to('/manager')
                
        except Exception as e:
            print(f"Login error: {e}")
            import traceback
            traceback.print_exc()
            ui.notify(f"Login error: {str(e)}", type="negative")
        finally:
            db.close()
    
    with ui.element('div').classes('fixed inset-0 flex items-center justify-center bg-gray-50'):
        with ui.card().classes('w-96 p-8 flex flex-col items-center justify-center'):
            ui.label('Aruba Bank').classes('text-3xl font-bold text-[#144c8e] mb-8 text-center')
            username_input = ui.input(label='Username').classes('w-full mb-4 text-center').props('outlined')
            password_input = ui.input(label='Password', password=True).classes('w-full mb-6 text-center').props('outlined')
            login_button = ui.button('Login', on_click=do_login).classes('w-full bg-[#144c8e] text-white')
            
            # Add Enter key support for both input fields
            username_input.on('keydown.enter', do_login)
            password_input.on('keydown.enter', do_login)
