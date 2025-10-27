"""Fix system36_variant values to uppercase to match enum"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3

# Get database path
db_path = "data/golf_tournament.db"

print("\n" + "="*60)
print("FIX: Update system36_variant values to match enum")
print("="*60 + "\n")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check current values
cursor.execute("SELECT id, name, system36_variant FROM event")
events = cursor.fetchall()

print("Current values:")
for event_id, name, variant in events:
    print(f"  Event {event_id}: {name} -> system36_variant='{variant}'")

# Update lowercase to uppercase (keeping the pattern)
print("\nUpdating values...")
cursor.execute("UPDATE event SET system36_variant = 'STANDARD' WHERE system36_variant = 'standard'")
cursor.execute("UPDATE event SET system36_variant = 'MODIFIED' WHERE system36_variant = 'modified'")

updated_rows = cursor.rowcount
conn.commit()

print(f"[OK] Updated {updated_rows} rows")

# Verify
cursor.execute("SELECT id, name, system36_variant FROM event")
events = cursor.fetchall()

print("\nUpdated values:")
for event_id, name, variant in events:
    print(f"  Event {event_id}: {name} -> system36_variant='{variant}'")

conn.close()

print("\n" + "="*60)
print("FIX COMPLETED")
print("="*60 + "\n")
