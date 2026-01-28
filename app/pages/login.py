from nicegui import app, ui
from app.db.database import SessionLocal
from app.models.contract import User, UserRole


def login_page():
    username_input = None
    password_input = None
    bank_select = None

    def do_login():
        # Validate mandatory fields
        if not bank_select or not bank_select.value:
            ui.notify("Please select a bank.", type="negative")
            return
        if not username_input or not username_input.value:
            ui.notify("Please enter a username.", type="negative")
            return
        if not password_input or not password_input.value:
            ui.notify("Please enter a password.", type="negative")
            return

        # Get username value after validation
        username = username_input.value

        # Look up user in database
        db = SessionLocal()
        try:
            # Try multiple matching strategies
            current_user = db.query(User).filter(User.email == username).first()
            if not current_user:
                current_user = (
                    db.query(User)
                    .filter(User.email.ilike(f"%{username}%"))
                    .first()
                )
            if not current_user:
                current_user = (
                    db.query(User)
                    .filter(User.first_name.ilike(f"%{username}%"))
                    .first()
                )
            if not current_user:
                current_user = (
                    db.query(User)
                    .filter(User.last_name.ilike(f"%{username}%"))
                    .first()
                )
            if not current_user and " " in username:
                parts = username.split()
                if len(parts) >= 2:
                    current_user = (
                        db.query(User)
                        .filter(
                            User.first_name.ilike(f"%{parts[0]}%"),
                            User.last_name.ilike(f"%{parts[-1]}%"),
                        )
                        .first()
                    )

            if not current_user:
                # Generic error text per AC
                ui.notify("Wrong username or password.", type="negative")
                return

            # NOTE: Password is currently not validated against the database.
            # To keep behavior consistent with existing data (no passwords),
            # we only enforce that a password was entered and use a generic error text above.

            # Store user info
            app.storage.user["logged_in"] = True
            app.storage.user["username"] = current_user.email
            app.storage.user["user_id"] = current_user.id
            app.storage.user["user_role"] = (
                current_user.role.value if current_user.role else None
            )

            # Navigate based on role
            if current_user.role == UserRole.CONTRACT_ADMIN:
                ui.navigate.to("/")
            elif current_user.role in [
                UserRole.CONTRACT_MANAGER,
                UserRole.CONTRACT_MANAGER_BACKUP,
                UserRole.CONTRACT_MANAGER_OWNER,
            ]:
                ui.navigate.to("/manager")
            else:
                # Default to manager page for unknown roles
                ui.navigate.to("/manager")

        except Exception as e:
            print(f"Login error: {e}")
            import traceback

            traceback.print_exc()
            ui.notify(f"Login error: {str(e)}", type="negative")
        finally:
            db.close()

    with ui.element("div").classes(
        "fixed inset-0 flex items-center justify-center bg-gray-50"
    ):
        with ui.card().classes(
            "w-[420px] p-8 flex flex-col items-center justify-center shadow-lg"
        ):
            # Logos row
            with ui.row().classes(
                "w-full justify-center items-center mb-6 gap-6"
            ):
                # served via /public from app/public
                ui.image("/public/AB Logo.png").classes(
                    "h-12 w-auto object-contain"
                )
                ui.image("/public/logo_ob.svg").classes(
                    "h-12 w-auto object-contain"
                )

            # Bank dropdown
            ui.label("Bank").classes("w-full text-left text-sm text-gray-600 mb-1")
            bank_select = ui.select(
                options=["Aruba Bank", "Orco Bank"],
                value=None,
                with_input=False,
            ).classes("w-full mb-4").props("outlined")

            # Username and password fields
            username_input = ui.input(label="Username").classes(
                "w-full mb-4"
            ).props("outlined")
            password_input = ui.input(
                label="Password",
                password=True,
                password_toggle_button=True,
            ).classes("w-full mb-6").props("outlined")

            # Login button
            ui.button("LOG IN", on_click=do_login).classes(
                "w-full bg-[#1976d2] text-white"
            )

            # Add Enter key support for both input fields
            username_input.on("keydown.enter", do_login)
            password_input.on("keydown.enter", do_login)
