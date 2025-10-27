"""
Migration: Add sub-division support to eventdivision table

Adds:
- parent_division_id (INTEGER, self-referential FK)
- is_auto_assigned (BOOLEAN)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3

def migrate():
    """Add sub-division support columns to eventdivision table"""

    print("\n" + "="*60)
    print("MIGRATION: Add sub-division support to eventdivision table")
    print("="*60 + "\n")

    db_path = "backend/data/golf_tournament.db"

    # Check if database exists
    if not os.path.exists(db_path):
        print(f"[ERROR] Database not found at {db_path}")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check existing columns
        cursor.execute("PRAGMA table_info(eventdivision)")
        columns = [col[1] for col in cursor.fetchall()]

        print("Current columns:", columns)
        print()

        # Add parent_division_id if missing
        if 'parent_division_id' not in columns:
            print("Adding column 'parent_division_id'...")
            cursor.execute("""
                ALTER TABLE eventdivision
                ADD COLUMN parent_division_id INTEGER DEFAULT NULL
                REFERENCES eventdivision(id)
            """)
            print("[OK] Column 'parent_division_id' added")
        else:
            print("[OK] Column 'parent_division_id' already exists")

        # Add is_auto_assigned if missing
        if 'is_auto_assigned' not in columns:
            print("Adding column 'is_auto_assigned'...")
            cursor.execute("""
                ALTER TABLE eventdivision
                ADD COLUMN is_auto_assigned BOOLEAN DEFAULT 0
            """)
            print("[OK] Column 'is_auto_assigned' added")
        else:
            print("[OK] Column 'is_auto_assigned' already exists")

        conn.commit()

        # Verify
        cursor.execute("PRAGMA table_info(eventdivision)")
        columns = [col[1] for col in cursor.fetchall()]

        print("\nUpdated columns:", columns)

        print("\n" + "="*60)
        print("MIGRATION COMPLETED")
        print("="*60 + "\n")

        conn.close()
        return True

    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()
        conn.close()
        return False


if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
