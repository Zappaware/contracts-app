"""
Breadcrumb navigation component.
Replaces "Back to Dashboard" and similar buttons with hierarchical breadcrumb navigation.
"""
from nicegui import ui
from app.utils.navigation import get_dashboard_url


def breadcrumb(items: list[tuple[str, str | None]]) -> None:
    """
    Render breadcrumb navigation.

    Args:
        items: List of (label, url) tuples. Last item should have url=None (current page).
               Example: [("Home", "/"), ("Vendors", "/vendors"), ("Acme Corp", None)]
    """
    if not items:
        return

    with ui.row().classes("items-center gap-1 text-sm text-gray-600 font-[segoe ui]"):
        for i, (label, url) in enumerate(items):
            if i > 0:
                ui.icon("chevron_right", size="xs").classes("text-gray-400")
            if url:
                ui.link(label, url).classes("no-underline text-gray-600 hover:text-black hover:underline")
            else:
                ui.label(label).classes("font-medium text-black")
