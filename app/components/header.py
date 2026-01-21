from nicegui import ui, app
from app.models.contract import UserRole
from app.utils.notifications import get_user_notifications, get_notification_count


def header():
    ui.link.default_classes(
        "no-underline text-base text-gray-500 items-center text-normal hover:underline font-[segoe ui] hover:text-black"
    )
    ui.dropdown_button.default_classes(
        "text-weight-regular normal-case text-gray-500 font-[segoe ui]"
    ).default_props("flat")
    with (
        ui.header()
        .classes(
            "bg-[#f8f9fa] p-2 font-[segoe ui] items-center flex flex-row justify-between"
        )
        .props("flat")
    ):
        # Left section: logo, navbar, dropdowns
        with ui.element("div").classes("flex flex-row items-center gap-3"):
            ui.link("Aruba Bank", "/").classes(
                "font-bold text-xl text-center mt-3 text-black w-32 h-[39px]"
            )

            # Home link - same styling as "New Contract"/"New Vendor", but role-based target
            user_role = app.storage.user.get('user_role', None)
            home_target = '/' if user_role == UserRole.CONTRACT_ADMIN.value else '/manager'
            ui.link("Home", home_target)
            ui.link("New Contract", "/new-contract")
            ui.link("New Vendor", "/new-vendor")
            with (
                ui.dropdown_button("Reports", auto_close=True, color=None)
                .classes(
                    "text-weight-regular normal-case text-gray-500 font-[segoe ui]"
                )
                .props("flat")
            ):
                ui.link("Active agreements", "/active-contracts").classes(
                    "text-black font-[segoe ui] flex flex-column p-2"
                )
                ui.link("Pending agreements", "/pending-contracts").classes(
                    "text-black font-[segoe ui] flex flex-column p-2"
                )
                ui.link("Expired agreements", "/expired-contracts").classes(
                    "text-black font-[segoe ui] flex flex-column p-2"
                )
                ui.link("Terminated agreements", "/terminated-contracts").classes(
                    "text-black font-[segoe ui] flex flex-column p-2"
                )
                ui.link("Material Outsourcing Agreement Report", "/moa-report").classes(
                    "text-black font-[segoe ui] flex flex-column p-2 border-t border-gray-200"
                )
                ui.link("Contracts Monetary Value Report", "/monetary-value-report").classes(
                    "text-black font-[segoe ui] flex flex-column p-2"
                )
                ui.link("Due Diligence Report", "/due-diligence-report").classes(
                    "text-black font-[segoe ui] flex flex-column p-2"
                )
                ui.menu_item("Audit trail").classes(
                    "text-black font-[segoe ui] flex flex-column p-2 border-t border-gray-200"
                )

            with (
                ui.dropdown_button("Advanced search", color=None)
                .props("flat")
                .classes(
                    "text-weight-regular normal-case text-gray-500 font-[segoe ui]"
                )
            ):
                with ui.column().classes("gap-2 p-2 min-w-[320px]"):
                    # Search mode
                    ui.label("Search mode").classes("text-xs font-semibold text-gray-700")
                    ui.select(["AND", "OR"], value="AND").classes("w-full")
                    # Contract ID
                    ui.label("Contract ID:").classes("text-xs font-semibold text-gray-700")
                    ui.input(placeholder="Enter contract ID").classes("w-full")
                    # Vendor
                    ui.label("Vendor:").classes("text-xs font-semibold text-gray-700")
                    ui.select(["Select a Vendor", "ABC Corp", "XYZ Services", "Acme Ltd"], value="Select a Vendor").classes("w-full")
                    # Type of Contract
                    ui.label("Type of Contract:").classes("text-xs font-semibold text-gray-700")
                    ui.select(["Select a contract type", "Service", "Supply", "Consulting"], value="Select a contract type").classes("w-full")
                    # Department
                    ui.label("Department:").classes("text-xs font-semibold text-gray-700")
                    ui.select(["Select a department", "Finance", "HR", "IT", "Legal"], value="Select a department").classes("w-full")
                    # Contract Start Date
                    ui.label("Contract Start Date:").classes("text-xs font-semibold text-gray-700")
                    with ui.input('Date') as date:
                        with ui.menu().props('no-parent-event') as menu:
                            with ui.date().bind_value(date):
                                with ui.row().classes('justify-end'):
                                    ui.button('Close', on_click=menu.close).props('flat')
                        with date.add_slot('append'):
                            ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer')
                    # Contract Expiration Date
                    ui.label("Contract Expiration Date:").classes("text-xs font-semibold text-gray-700")
                    with ui.input('Date') as exp_date:
                        with ui.menu().props('no-parent-event') as menu:
                            with ui.date().bind_value(exp_date):
                                with ui.row().classes('justify-end'):
                                    ui.button('Close', on_click=menu.close).props('flat')
                        with exp_date.add_slot('append'):
                            ui.icon('edit_calendar').on('click', menu.open).classes('cursor-pointer')
                    # Buttons
                    with ui.row().classes("gap-2 pt-2"):
                        ui.button("Search", color="primary").classes("w-24")
                        ui.button("Clear", color=None).classes("w-24")

        # Spacer to push right section to the end
        ui.element("div").classes("flex-grow")

        # Right section: notifications bell and logout button
        with ui.element("div").classes("flex flex-row items-center gap-4"):
            # Notification bell icon with badge
            notifications = get_user_notifications()
            notification_count = len(notifications)
            
            # Notification bell button with badge
            with ui.element("div").classes("relative"):
                notification_btn = ui.button(icon="notifications", color=None).classes(
                    "text-weight-regular normal-case text-gray-500 font-[segoe ui]"
                ).props("flat")
                
                # Badge showing notification count
                if notification_count > 0:
                    badge_text = str(notification_count) if notification_count <= 99 else "99+"
                    with ui.element("span").classes(
                        "absolute -top-1 -right-1 bg-red-500 text-white text-xs font-bold rounded-full"
                    ).style("width: 18px; height: 18px; display: flex; align-items: center; justify-content: center; z-index: 10;"):
                        ui.label(badge_text).classes("text-[10px]")
            
            # Notification dropdown menu
            with ui.menu().props('anchor=bottom right') as notification_menu:
                with ui.card().classes("min-w-[400px] max-w-[500px] max-h-[600px] overflow-y-auto"):
                    ui.label("Notifications").classes("text-h6 font-bold mb-4 p-4 border-b")
                    
                    if notification_count == 0:
                        with ui.column().classes("p-6 items-center gap-2"):
                            ui.icon("notifications_off", size="48px", color="gray")
                            ui.label("No notifications").classes("text-gray-500")
                    else:
                        with ui.column().classes("gap-2 p-2"):
                            for idx, notif in enumerate(notifications[:10]):  # Show max 10 notifications
                                priority = notif.get("priority", "low")
                                priority_colors = {
                                    "high": "border-l-red-500 bg-red-50",
                                    "medium": "border-l-orange-500 bg-orange-50",
                                    "low": "border-l-blue-500 bg-blue-50"
                                }
                                border_color = priority_colors.get(priority, "border-l-gray-500 bg-gray-50")
                                
                                # Create clickable notification card
                                notif_link = notif.get("link", "#")
                                
                                # Use lambda with default parameter to capture the link value correctly
                                def make_click_handler(link=notif_link):
                                    def handle_click():
                                        notification_menu.close()
                                        if link and link != "#":
                                            ui.navigate.to(link)
                                    return handle_click
                                
                                with ui.card().classes(f"p-3 cursor-pointer hover:bg-gray-100 border-l-4 {border_color}").style("min-width: 100%;") as notif_card:
                                    notif_card.on_click(make_click_handler())
                                    with ui.column().classes("gap-1"):
                                        ui.label(notif.get("title", "Notification")).classes("font-semibold text-sm")
                                        ui.label(notif.get("message", "")).classes("text-xs text-gray-600")
                            
                            if notification_count > 10:
                                ui.label(f"... and {notification_count - 10} more").classes("text-xs text-gray-500 text-center p-2")
            
            # Open notification menu when bell is clicked
            notification_btn.on_click(notification_menu.open)
            
            # Logout button with confirmation dialog
            logout_btn = ui.button("Logout", color=None, icon="logout").classes(
                "text-weight-regular normal-case text-gray-500 font-[segoe ui]"
            ).props("flat")
            
            # Logout confirmation dialog
            with ui.dialog() as logout_dialog, ui.card().classes("min-w-[400px]"):
                ui.label("Confirm Logout").classes("text-h6 mb-4 font-bold")
                ui.label("Are you sure you want to log out?").classes("mb-6 text-gray-700")
                
                with ui.row().classes("gap-2 justify-end w-full"):
                    cancel_btn = ui.button("Cancel", on_click=logout_dialog.close).props('flat color=grey')
                    
                    def confirm_logout():
                        """Perform logout: clear session and redirect to login"""
                        # Close dialog first
                        logout_dialog.close()
                        
                        # Clear all user session data
                        app.storage.user.clear()
                        # Explicitly mark as not logged in
                        app.storage.user['logged_in'] = False
                        
                        # Clear browser storage and redirect with session invalidation
                        ui.run_javascript('''
                            // Clear session storage
                            if (typeof(Storage) !== "undefined") {
                                sessionStorage.clear();
                            }
                            // Clear NiceGUI user storage from local storage
                            try {
                                localStorage.removeItem('nicegui_user_storage');
                            } catch(e) {
                                console.log('Could not clear localStorage:', e);
                            }
                            // Replace current history entry to prevent back button access
                            window.history.replaceState(null, null, '/login');
                            // Force redirect to login page (this prevents back button access)
                            window.location.replace('/login');
                        ''')
                        
                        # Also use NiceGUI navigation as immediate fallback
                        # Using replace instead of navigate to prevent back button access
                        try:
                            ui.navigate.to('/login', replace=True)
                        except:
                            # If replace doesn't work, use regular navigate
                            ui.navigate.to('/login')
                    
                    confirm_btn = ui.button("Logout", icon="logout", on_click=confirm_logout).props('color=negative')
            
            # Open logout confirmation dialog when logout button is clicked
            logout_btn.on_click(logout_dialog.open)