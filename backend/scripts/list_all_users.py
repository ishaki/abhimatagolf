#!/usr/bin/env python3
"""
Script to list all users in the database
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select
from core.database import engine
from models.user import User

def list_all_users():
    """List all users in the database"""

    print("\n" + "="*70)
    print("ALL USERS IN DATABASE")
    print("="*70)

    with Session(engine) as session:
        users = session.exec(select(User)).all()

        if not users:
            print("\nNo users found in database!")
            return

        print(f"\nTotal Users: {len(users)}\n")
        print(f"{'ID':<5} {'Full Name':<30} {'Email':<35} {'Role':<15} {'Active'}")
        print("-" * 70)

        for user in users:
            active_str = "Yes" if user.is_active else "No"
            print(f"{user.id:<5} {user.full_name:<30} {user.email:<35} {user.role.value:<15} {active_str}")

        print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    list_all_users()
