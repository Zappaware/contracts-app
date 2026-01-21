"""
Utility functions for fetching user notifications.
"""
from datetime import date, timedelta
from nicegui import app
from app.db.database import SessionLocal
from app.models.contract import Contract, ContractStatusType, ContractUpdate, ContractUpdateStatus, UserRole
from sqlalchemy import or_, and_
from sqlalchemy.orm import joinedload
import re


def get_user_notifications():
    """
    Fetch notifications for the current logged-in user based on their role.
    
    Returns a list of notification dictionaries with:
    - type: notification type (expiring_soon, past_due, pending_review, etc.)
    - title: notification title
    - message: notification message
    - link: optional link to related page
    - priority: high, medium, low
    - timestamp: when the notification was generated
    """
    notifications = []
    
    try:
        current_user_id = app.storage.user.get('user_id', None)
        user_role = app.storage.user.get('user_role', None)
        
        if not current_user_id:
            return notifications
        
        db = SessionLocal()
        try:
            today = date.today()
            
            # For Contract Managers and Backups: Show contracts expiring soon or past due
            if user_role in [UserRole.CONTRACT_MANAGER.value, UserRole.CONTRACT_MANAGER_BACKUP.value, UserRole.CONTRACT_MANAGER_OWNER.value]:
                # Get active contracts where user is owner or backup
                contracts = db.query(Contract).options(
                    joinedload(Contract.vendor),
                    joinedload(Contract.contract_owner),
                    joinedload(Contract.contract_owner_backup)
                ).filter(
                    Contract.status == ContractStatusType.ACTIVE,
                    or_(
                        Contract.contract_owner_id == current_user_id,
                        Contract.contract_owner_backup_id == current_user_id
                    )
                ).all()
                
                for contract in contracts:
                    if not contract.end_date:
                        continue
                    
                    # Parse expiration notice frequency to get days
                    notice_days = 30  # Default
                    if contract.expiration_notice_frequency:
                        freq_str = contract.expiration_notice_frequency.value if hasattr(contract.expiration_notice_frequency, 'value') else str(contract.expiration_notice_frequency)
                        match = re.search(r'(\d+)', freq_str)
                        if match:
                            notice_days = int(match.group(1))
                    
                    # Calculate notification window start date
                    notification_window_date = contract.end_date - timedelta(days=notice_days)
                    days_diff = (contract.end_date - today).days
                    
                    # Determine user's role for this contract
                    if contract.contract_owner_id == current_user_id:
                        role_text = "Contract Manager"
                    elif contract.contract_owner_backup_id == current_user_id:
                        role_text = "Backup"
                    else:
                        continue
                    
                    vendor_name = contract.vendor.vendor_name if contract.vendor else "Unknown"
                    
                    if days_diff < 0:
                        # Past due - HIGH priority
                        notifications.append({
                            "type": "past_due",
                            "title": f"Contract {contract.contract_id} is Past Due",
                            "message": f"{contract.contract_id} with {vendor_name} expired {abs(days_diff)} day(s) ago. Action required.",
                            "link": f"/contract-info/{contract.id}",
                            "priority": "high",
                            "timestamp": today,
                            "contract_id": contract.contract_id,
                        })
                    elif today >= notification_window_date:
                        # Approaching expiration - MEDIUM priority
                        notifications.append({
                            "type": "expiring_soon",
                            "title": f"Contract {contract.contract_id} Expiring Soon",
                            "message": f"{contract.contract_id} with {vendor_name} expires in {days_diff} day(s). Your role: {role_text}.",
                            "link": f"/contract-info/{contract.id}",
                            "priority": "medium",
                            "timestamp": today,
                            "contract_id": contract.contract_id,
                        })
            
            # For Contract Admins: Show pending reviews
            if user_role == UserRole.CONTRACT_ADMIN.value:
                # Get pending contract updates
                pending_updates = db.query(ContractUpdate).options(
                    joinedload(ContractUpdate.contract).joinedload(Contract.vendor)
                ).filter(
                    ContractUpdate.status == ContractUpdateStatus.PENDING_REVIEW
                ).all()
                
                for update in pending_updates:
                    contract = update.contract
                    vendor_name = contract.vendor.vendor_name if contract.vendor else "Unknown"
                    
                    notifications.append({
                        "type": "pending_review",
                        "title": f"Contract Update Pending Review",
                        "message": f"Update for {contract.contract_id} ({vendor_name}) requires your review.",
                        "link": "/contract-updates",
                        "priority": "high",
                        "timestamp": update.created_at.date() if update.created_at else today,
                        "contract_id": contract.contract_id,
                    })
                
                # Also check for contracts expiring soon (admin overview)
                expiring_contracts = db.query(Contract).options(
                    joinedload(Contract.vendor)
                ).filter(
                    Contract.status == ContractStatusType.ACTIVE,
                    Contract.end_date <= today + timedelta(days=30),
                    Contract.end_date >= today
                ).limit(5).all()
                
                for contract in expiring_contracts:
                    if not contract.end_date:
                        continue
                    
                    days_diff = (contract.end_date - today).days
                    vendor_name = contract.vendor.vendor_name if contract.vendor else "Unknown"
                    
                    notifications.append({
                        "type": "expiring_soon",
                        "title": f"Contract {contract.contract_id} Expiring Soon",
                        "message": f"{contract.contract_id} with {vendor_name} expires in {days_diff} day(s).",
                        "link": f"/contract-info/{contract.id}",
                        "priority": "medium",
                        "timestamp": today,
                        "contract_id": contract.contract_id,
                    })
            
        finally:
            db.close()
    except Exception as e:
        print(f"Error fetching notifications: {e}")
        import traceback
        traceback.print_exc()
    
    # Sort by priority (high first) and then by timestamp (newest first)
    priority_order = {"high": 0, "medium": 1, "low": 2}
    notifications.sort(key=lambda x: (priority_order.get(x.get("priority", "low"), 2), x.get("timestamp", date.min)), reverse=True)
    
    return notifications


def get_notification_count():
    """Get the count of unread notifications for the current user."""
    notifications = get_user_notifications()
    return len(notifications)
