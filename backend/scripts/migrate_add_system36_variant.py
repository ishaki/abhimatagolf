"""
Migration: Add system36_variant column to event table

This migration adds the system36_variant column to the event table.
Default value is 'standard' for existing events.
"""

import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session
from core.database import engine
import sqlite3

def migrate():
    """Add system36_variant column to event table"""

    print("\n" + "="*60)
    print("MIGRATION: Add system36_variant column to event table")
    print("="*60 + "\n")

    # Get the database path from the engine
    db_path = str(engine.url).replace('sqlite:///', '')

    try:
        # Connect directly to SQLite
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if column already exists
        cursor.execute("PRAGMA table_info(event)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'system36_variant' in columns:
            print("[OK] Column 'system36_variant' already exists in event table")
            print("    No migration needed.")
            conn.close()
            return True

        print("Adding column 'system36_variant' to event table...")

        # Add the column with default value 'STANDARD' (uppercase to match enum)
        cursor.execute("""
            ALTER TABLE event
            ADD COLUMN system36_variant VARCHAR DEFAULT 'STANDARD'
        """)

        conn.commit()
        print("[OK] Column added successfully")

        # Verify the column was added
        cursor.execute("PRAGMA table_info(event)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'system36_variant' in columns:
            print("[OK] Migration verified - column exists")

            # Count existing events
            cursor.execute("SELECT COUNT(*) FROM event")
            count = cursor.fetchone()[0]
            print(f"[OK] {count} existing event(s) will use default value 'STANDARD'")
        else:
            print("[ERROR] Column was not added!")
            conn.close()
            return False

        conn.close()

        print("\n" + "="*60)
        print("MIGRATION COMPLETED SUCCESSFULLY")
        print("="*60 + "\n")

        return True

    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
