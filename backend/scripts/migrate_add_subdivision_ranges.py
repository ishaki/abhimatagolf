"""
Migration: Add subdivision_ranges to winner_configuration table

Adds:
- subdivision_ranges (JSON field for auto-assigned sub-divisions)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3

def migrate():
    """Add subdivision_ranges column to winner_configuration table"""

    print("\n" + "="*60)
    print("MIGRATION: Add subdivision_ranges to winner_configuration")
    print("="*60 + "\n")

    db_path = "backend/data/golf_tournament.db"

    # Check if database exists
    if not os.path.exists(db_path):
        print(f"[ERROR] Database not found at {db_path}")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if winner_configuration table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='winnerconfiguration'
        """)
        table_exists = cursor.fetchone()

        if not table_exists:
            print("[INFO] Table 'winnerconfiguration' does not exist yet")
            print("[INFO] It will be created when first winner configuration is saved")
            print("[OK] No migration needed at this time")
            conn.close()
            return True

        # Check existing columns
        cursor.execute("PRAGMA table_info(winnerconfiguration)")
        columns = [col[1] for col in cursor.fetchall()]

        print("Current columns:", columns)
        print()

        # Add subdivision_ranges if missing
        if 'subdivision_ranges' not in columns:
            print("Adding column 'subdivision_ranges'...")
            cursor.execute("""
                ALTER TABLE winnerconfiguration
                ADD COLUMN subdivision_ranges TEXT DEFAULT NULL
            """)
            print("[OK] Column 'subdivision_ranges' added")
        else:
            print("[OK] Column 'subdivision_ranges' already exists")

        conn.commit()

        # Verify
        cursor.execute("PRAGMA table_info(winnerconfiguration)")
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
