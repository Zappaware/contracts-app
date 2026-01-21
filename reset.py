#!/usr/bin/env python3
"""
Script to reset the database by dropping all tables and cleaning uploads directory.
Useful for testing - allows you to re-run seed scripts from scratch.
"""
import os
import shutil
from sqlalchemy import text
from app.db.database import engine, Base
from app.models.vendor import Vendor, VendorAddress, VendorEmail, VendorPhone, VendorDocument
from app.models.contract import Contract, ContractDocument, User


def reset_database():
    """
    Drop all tables from the database to reset it to a clean state.
    """
    print("🔄 Resetting database...")
    
    try:
        # Import all models to ensure they're registered with Base.metadata
        from app.models import vendor, contract
        
        # Drop all tables
        print("  Dropping all tables...")
        Base.metadata.drop_all(bind=engine)
        print("  ✓ All tables dropped")
        
        # Also drop the alembic_version table if it exists (to reset migration tracking)
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE"))
            conn.commit()
        print("  ✓ Alembic version table dropped")
        
        print("\n✅ Database reset complete!")
        print("   You can now run:")
        print("   1. alembic upgrade head  (to recreate tables)")
        print("   2. python seed_users.py  (to seed users)")
        print("   3. python seed_vendors_contracts.py  (to seed vendors and contracts)")
        
    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        import traceback
        traceback.print_exc()
        raise


def clean_uploads():
    """
    Clean the uploads directory (removes all uploaded files).
    """
    uploads_dir = "uploads"
    
    if os.path.exists(uploads_dir):
        print(f"\n🧹 Cleaning uploads directory ({uploads_dir})...")
        try:
            # Remove all contents but keep the directory
            for item in os.listdir(uploads_dir):
                item_path = os.path.join(uploads_dir, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
            print("  ✓ Uploads directory cleaned")
        except Exception as e:
            print(f"  ⚠️  Warning: Could not clean uploads directory: {e}")
    else:
        print(f"\n  ℹ️  Uploads directory ({uploads_dir}) does not exist, skipping...")


def reset_all():
    """
    Reset both database and uploads directory.
    """
    print("=" * 60)
    print("DATABASE RESET UTILITY")
    print("=" * 60)
    print("\n⚠️  WARNING: This will delete ALL data from the database!")
    print("   This includes:")
    print("   - All users")
    print("   - All vendors")
    print("   - All contracts")
    print("   - All documents")
    print("   - All uploaded files")
    print("\n" + "=" * 60)
    print("\n🔄 Proceeding with reset...\n")
    reset_database()
    clean_uploads()
    
    print("\n" + "=" * 60)
    print("✅ RESET COMPLETE")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Run: alembic upgrade head")
    print("  2. Run: python seed_users.py")
    print("  3. Run: python seed_vendors_contracts.py")
    print()


if __name__ == "__main__":
    reset_all()

