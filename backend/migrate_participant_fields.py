"""
Database migration script to add new participant fields.

This script adds the following fields to the participant table:
- country (optional string)
- sex (optional string)
- phone_no (optional string)
- event_status (string, default 'Ok')
- event_description (optional string)

Run this script before starting the application with the updated models.
"""

import sqlite3
import os
from pathlib import Path

# Get the database path
DB_PATH = Path(__file__).parent / "data" / "golf_tournament.db"

def migrate_database():
    """Add new fields to participant table."""
    
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        print("This is expected for a new installation.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(participant)")
        columns = [column[1] for column in cursor.fetchall()]
        
        migrations = []
        
        # Add country column if it doesn't exist
        if 'country' not in columns:
            migrations.append(("country", "ALTER TABLE participant ADD COLUMN country VARCHAR(100)"))
        
        # Add sex column if it doesn't exist
        if 'sex' not in columns:
            migrations.append(("sex", "ALTER TABLE participant ADD COLUMN sex VARCHAR(10)"))
        
        # Add phone_no column if it doesn't exist
        if 'phone_no' not in columns:
            migrations.append(("phone_no", "ALTER TABLE participant ADD COLUMN phone_no VARCHAR(20)"))
        
        # Add event_status column if it doesn't exist
        if 'event_status' not in columns:
            migrations.append(("event_status", "ALTER TABLE participant ADD COLUMN event_status VARCHAR(50) DEFAULT 'Ok'"))
        
        # Add event_description column if it doesn't exist
        if 'event_description' not in columns:
            migrations.append(("event_description", "ALTER TABLE participant ADD COLUMN event_description VARCHAR(500)"))
        
        if not migrations:
            print("[OK] All participant fields already exist. No migration needed.")
            return
        
        # Apply migrations
        print(f"[INFO] Applying {len(migrations)} migration(s)...")
        for field_name, sql in migrations:
            print(f"   Adding column: {field_name}")
            cursor.execute(sql)
        
        conn.commit()
        print(f"[OK] Successfully migrated {len(migrations)} field(s) to participant table")
        
        # Update existing records to have default event_status
        if 'event_status' in [m[0] for m in migrations]:
            cursor.execute("UPDATE participant SET event_status = 'Ok' WHERE event_status IS NULL")
            conn.commit()
            print("[OK] Updated existing participants with default event_status='Ok'")
        
    except Exception as e:
        print(f"[ERROR] Error during migration: {str(e)}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Participant Fields Migration Script")
    print("=" * 60)
    migrate_database()
    print("=" * 60)
    print("Migration complete!")
    print("\nNew fields added:")
    print("  - country (optional)")
    print("  - sex (Male/Female, optional)")
    print("  - phone_no (optional)")
    print("  - event_status (Ok/No Show/Disqualified, default: Ok)")
    print("  - event_description (optional)")
    print("=" * 60)

