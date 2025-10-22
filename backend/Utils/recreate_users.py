#!/usr/bin/env python3
"""
Recreate Users Script
====================

This script recreates users in the database with proper roles:
- 1 Super Admin
- 1 Event Admin

Usage:
    python recreate_users.py
"""

import sys
from pathlib import Path
from passlib.context import CryptContext

# Add the backend directory to the Python path
sys.path.append(str(Path(__file__).parent))

from core.database import get_session
from models.user import User, UserRole
from sqlmodel import select, delete


def recreate_users():
    """Recreate users with proper roles"""
    
    print("Starting user recreation...")
    
    try:
        # Get database session
        session = next(get_session())
        
        # Clear existing users
        print("Clearing existing users...")
        delete_query = delete(User)
        session.exec(delete_query)
        session.commit()
        
        # Password hashing context
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # Create Super Admin
        print("Creating Super Admin...")
        super_admin = User(
            full_name="Super Administrator",
            email="admin@abhimatagolf.com",
            hashed_password=pwd_context.hash("admin123"),
            role=UserRole.SUPER_ADMIN,
            is_active=True
        )
        session.add(super_admin)
        
        # Create Event Admin
        print("Creating Event Admin...")
        event_admin = User(
            full_name="Event Administrator",
            email="eventadmin@abhimatagolf.com",
            hashed_password=pwd_context.hash("eventadmin123"),
            role=UserRole.EVENT_ADMIN,
            is_active=True
        )
        session.add(event_admin)
        
        # Commit changes
        session.commit()
        
        # Verify creation
        users_query = select(User)
        users = session.exec(users_query).all()
        
        print(f"User recreation completed successfully!")
        print(f"Total users created: {len(users)}")
        
        print("\nCreated users:")
        for user in users:
            print(f"  {user.id}: {user.email} - {user.role.value} - Active: {user.is_active}")
        
        print("\nLogin credentials:")
        print("  Super Admin:")
        print("    Email: admin@abhimatagolf.com")
        print("    Password: admin123")
        print("  Event Admin:")
        print("    Email: eventadmin@abhimatagolf.com")
        print("    Password: eventadmin123")
        
    except Exception as e:
        print(f"ERROR during user recreation: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    recreate_users()
