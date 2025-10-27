"""
Migration: Add missing columns to eventdivision table

Adds:
- division_type (VARCHAR)
- use_course_handicap_for_assignment (BOOLEAN)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3

def migrate():
    """Add missing columns to eventdivision table"""

    print("\n" + "="*60)
    print("MIGRATION: Add columns to eventdivision table")
    print("="*60 + "\n")

    db_path = "backend/data/golf_tournament.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check existing columns
        cursor.execute("PRAGMA table_info(eventdivision)")
        columns = [col[1] for col in cursor.fetchall()]

        print("Current columns:", columns)
        print()

        # Add division_type if missing
        if 'division_type' not in columns:
            print("Adding column 'division_type'...")
            cursor.execute("""
                ALTER TABLE eventdivision
                ADD COLUMN division_type VARCHAR DEFAULT NULL
            """)
            print("[OK] Column 'division_type' added")
        else:
            print("[OK] Column 'division_type' already exists")

        # Add use_course_handicap_for_assignment if missing
        if 'use_course_handicap_for_assignment' not in columns:
            print("Adding column 'use_course_handicap_for_assignment'...")
            cursor.execute("""
                ALTER TABLE eventdivision
                ADD COLUMN use_course_handicap_for_assignment BOOLEAN DEFAULT 0
            """)
            print("[OK] Column 'use_course_handicap_for_assignment' added")
        else:
            print("[OK] Column 'use_course_handicap_for_assignment' already exists")

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
