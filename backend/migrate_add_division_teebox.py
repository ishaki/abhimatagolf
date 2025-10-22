#!/usr/bin/env python3
"""
Database migration script to add teebox_id column to eventdivision table.
This script should be run after the teebox table has been created.
"""

import sqlite3
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from core.database import engine
from sqlmodel import Session, select, text

def add_teebox_column():
    """Add teebox_id column to eventdivision table"""
    print("Adding teebox_id column to eventdivision table...")

    try:
        with engine.connect() as conn:
            # Check if column already exists
            result = conn.execute(text("PRAGMA table_info(eventdivision)"))
            columns = [row[1] for row in result]

            if 'teebox_id' in columns:
                print("Column teebox_id already exists in eventdivision table, skipping")
                return

            # Add the column
            conn.execute(text("""
                ALTER TABLE eventdivision
                ADD COLUMN teebox_id INTEGER REFERENCES teebox(id)
            """))
            conn.commit()

        print("Successfully added teebox_id column to eventdivision table")

    except Exception as e:
        print(f"Error adding column: {e}")
        raise

def verify_migration():
    """Verify the migration was successful"""
    print("Verifying migration...")

    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(eventdivision)"))
        columns = {row[1]: row[2] for row in result}

        if 'teebox_id' in columns:
            print(f"[OK] Column teebox_id found with type: {columns['teebox_id']}")
            print("Migration verification successful!")
        else:
            print("[ERROR] Column teebox_id not found")
            sys.exit(1)

def main():
    """Run the migration"""
    print("Starting eventdivision teebox migration...")
    print("=" * 50)

    try:
        add_teebox_column()
        verify_migration()

        print("=" * 50)
        print("Migration completed successfully!")

    except Exception as e:
        print(f"Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
