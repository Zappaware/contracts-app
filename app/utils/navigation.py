"""
Utility functions for navigation based on user roles.
"""
from nicegui import app


def get_dashboard_url() -> str:
    """
    Get the appropriate dashboard URL based on the current user's role.
    
    Returns:
        '/manager' for Contract Manager roles
        '/' for Contract Admin role
        '/manager' as default if role is unknown
    """
    user_role = app.storage.user.get('user_role', None)
    
    # Contract Admin goes to admin dashboard
    if user_role == "Contract Admin":
        return '/'
    
    # All manager roles go to manager dashboard
    # This includes: Contract Manager, Contract Manager Backup, Contract Manager Owner
    return '/manager'
