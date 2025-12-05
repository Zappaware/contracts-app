"""
Utility function to look up vendor_id from vendor_name.
This is useful for pages that have vendor_name but need vendor_id for routing.
"""


def get_vendor_id_by_name(vendor_name: str) -> int:
    """
    Helper function to get vendor_id from vendor_name.
    Returns None if vendor not found.
    """
    try:
        from app.db.database import SessionLocal
        from app.models.vendor import Vendor
        
        db = SessionLocal()
        try:
            vendor = db.query(Vendor).filter(Vendor.vendor_name == vendor_name).first()
            if vendor:
                return vendor.id
            return None
        finally:
            db.close()
    except Exception as e:
        print(f"Error looking up vendor: {e}")
        return None

