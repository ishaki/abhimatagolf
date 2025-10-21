#!/usr/bin/env python3
"""
Simple script to create a test user for login testing
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlmodel import Session, select
from core.database import engine
from core.security import get_password_hash
from models.user import User, UserRole

def create_test_user():
    """Create a test user for login testing"""
    
    with Session(engine) as session:
        # Check if test user already exists
        user_statement = select(User).where(User.email == "admin@abhimatagolf.com")
        existing_user = session.exec(user_statement).first()
        
        if not existing_user:
            # Create test user
            test_user = User(
                full_name="Super Admin",
                email="admin@abhimatagolf.com",
                hashed_password=get_password_hash("admin123"),
                role=UserRole.SUPER_ADMIN,
                is_active=True
            )
            
            session.add(test_user)
            session.commit()
            print("✅ Test user created successfully!")
            print("Email: admin@abhimatagolf.com")
            print("Password: admin123")
        else:
            print("✅ Test user already exists!")
            print("Email: admin@abhimatagolf.com")
            print("Password: admin123")

if __name__ == "__main__":
    create_test_user()
