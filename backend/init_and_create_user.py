#!/usr/bin/env python3
"""
Script to initialize database and create test user
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlmodel import SQLModel, Session, select
from core.database import engine
from core.security import get_password_hash
from models.user import User, UserRole
from models.course import Course, Hole
from models.event import Event
from models.participant import Participant
from models.scorecard import Scorecard
from models.user_event import UserEvent
from models.leaderboard_cache import LeaderboardCache
from seed_data import create_seed_courses

def init_database():
    """Initialize database with all tables"""
    print("Creating database tables...")
    SQLModel.metadata.create_all(engine)
    print("Database tables created successfully!")

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
            print("Test user created successfully!")
            print("   Email: admin@abhimatagolf.com")
            print("   Password: admin123")
        else:
            print("Test user already exists!")
            print("   Email: admin@abhimatagolf.com")
            print("   Password: admin123")


        if not existing_user:
            # Create test user
            test_user = User(
                full_name="Event Admin",
                email="eventadmin@abhimatagolf.com",
                hashed_password=get_password_hash("event123"),
                role=UserRole.SUPER_ADMIN,
                is_active=True
            )
            session.add(test_user)
            session.commit()
            print("Test user created successfully!")
            print("   Email: eventadmin@abhimatagolf.com")
            print("   Password: event123")
        else:
            print("Test user already exists!")
            print("   Email: eventadmin@abhimatagolf.com")
            print("   Password: event123")

if __name__ == "__main__":
    init_database()
    create_test_user()
    create_seed_courses()
