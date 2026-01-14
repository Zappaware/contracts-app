#!/usr/bin/env python3
"""
Script to seed initial users into the database
"""
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.contract import User, DepartmentType, UserRole
from app.core.security import get_password_hash
from datetime import datetime, timezone

def seed_users():
    db = SessionLocal()
    
    try:
        # Check if users already exist
        existing_count = db.query(User).count()
        if existing_count > 0:
            print(f"⚠️  Database already has {existing_count} user(s). Skipping seed.")
            return
        
        # Create 5 initial users
        users_data = [
            {
                "user_id": "U1",
                "first_name": "William",
                "last_name": "Defoe",
                "email": "william.defoe@arubabank.com",
                "department": DepartmentType.IT,
                "position": "IT Manager",
                "role": UserRole.CONTRACT_ADMIN,
                "password": "password123"
            },
            {
                "user_id": "U2",
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@arubabank.com",
                "department": DepartmentType.OPERATIONS,
                "position": "Operations Manager",
                "role": UserRole.CONTRACT_MANAGER,
                "password": "password123"
            },
            {
                "user_id": "U3",
                "first_name": "Jane",
                "last_name": "Smith",
                "email": "jane.smith@arubabank.com",
                "department": DepartmentType.FINANCE,
                "position": "Finance Manager",
                "role": UserRole.CONTRACT_MANAGER_BACKUP,
                "password": "password123"
            },
            {
                "user_id": "U4",
                "first_name": "Robert",
                "last_name": "Johnson",
                "email": "robert.johnson@arubabank.com",
                "department": DepartmentType.LEGAL,
                "position": "Legal Manager",
                "role": UserRole.CONTRACT_MANAGER,
                "password": "password123"
            },
            {
                "user_id": "U5",
                "first_name": "Maria",
                "last_name": "Lopez",
                "email": "maria.lopez@arubabank.com",
                "department": DepartmentType.OPERATIONS,
                "position": "Contract Manager Owner",
                "role": UserRole.CONTRACT_MANAGER_OWNER,
                "password": "password123"
            }
        ]
        
        print("🌱 Seeding users...")
        
        for user_data in users_data:
            password = user_data.pop("password")
            user = User(
                **user_data,
                hashed_password=get_password_hash(password),
                is_active=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db.add(user)
            print(f"  ✓ Created user: {user.first_name} {user.last_name} ({user.email})")
        
        db.commit()
        print("\n✅ Successfully seeded 5 users!")
        print("\nYou can now login with:")
        print("  Admin: william.defoe@arubabank.com")
        print("  Manager: john.doe@arubabank.com or robert.johnson@arubabank.com")
        print("  Owner: maria.lopez@arubabank.com")
        print("  Backup: jane.smith@arubabank.com")
        print("  Password for all: password123")
        
    except Exception as e:
        print(f"❌ Error seeding users: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_users()

