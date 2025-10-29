"""
Migration: Add division reassignment tracking fields to winner_result table

This migration adds:
- original_division_id: Tracks the original division before reassignment
- division_reassigned: Boolean flag to indicate if division was changed

These fields support System 36 Modified validation where participants
may be reassigned to different divisions based on calculated handicap.
"""

import sqlite3
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.config import settings


def migrate():
    """Add division reassignment tracking fields to winner_result table"""

    # Connect to database
    conn = sqlite3.connect(settings.database_url.replace('sqlite:///', ''))
    cursor = conn.cursor()

    print("MIGRATION: Add division reassignment tracking to winner_result table")
    print("=" * 80)

    try:
        # Check if table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='winnerresult'
        """)

        if not cursor.fetchone():
            print("[ERROR] Table 'winnerresult' does not exist")
            return

        # Get current columns
        cursor.execute("PRAGMA table_info(winnerresult)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"Current columns in winnerresult: {', '.join(columns)}")
        print()

        # Check if columns already exist
        if 'original_division_id' in columns and 'division_reassigned' in columns:
            print("[OK] Columns 'original_division_id' and 'division_reassigned' already exist")
            return

        # Add original_division_id column if not exists
        if 'original_division_id' not in columns:
            print("Adding column 'original_division_id' to winnerresult table...")
            cursor.execute("""
                ALTER TABLE winnerresult
                ADD COLUMN original_division_id INTEGER
            """)
            print("[SUCCESS] Added 'original_division_id' column")
        else:
            print("[OK] Column 'original_division_id' already exists")

        # Add division_reassigned column if not exists
        if 'division_reassigned' not in columns:
            print("Adding column 'division_reassigned' to winnerresult table...")
            cursor.execute("""
                ALTER TABLE winnerresult
                ADD COLUMN division_reassigned BOOLEAN DEFAULT 0
            """)
            print("[SUCCESS] Added 'division_reassigned' column")
        else:
            print("[OK] Column 'division_reassigned' already exists")

        # Commit changes
        conn.commit()
        print()
        print("=" * 80)
        print("[SUCCESS] Migration completed successfully")

        # Verify columns were added
        cursor.execute("PRAGMA table_info(winnerresult)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"Updated columns in winnerresult: {', '.join(columns)}")

    except sqlite3.Error as e:
        print(f"[ERROR] Database error: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    migrate()
