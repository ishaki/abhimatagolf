#!/usr/bin/env python3
"""
Restore Participants to Event ID 1
==================================

This script restores participants from the backup file to Event ID 1.
It will clear existing participants and restore from backup.

Usage:
    python restore_participants_event1.py

Make sure backup_participants_event1.json exists in the same directory.
"""

import json
import sys
from pathlib import Path

# Add the backend directory to the Python path
sys.path.append(str(Path(__file__).parent))

from core.database import get_session
from models.participant import Participant
from sqlmodel import select, delete


def restore_participants():
    """Restore participants from backup file"""
    
    print("Starting restore of participants to Event ID 1...")
    
    try:
        # Check if backup file exists
        backup_file = Path("backup_participants_event1.json")
        if not backup_file.exists():
            print(f"ERROR: Backup file not found: {backup_file}")
            print("Please run backup_participants_event1.py first")
            return
        
        # Load backup data
        with open(backup_file, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        participants_data = backup_data.get("participants", [])
        backup_info = backup_data.get("backup_info", {})
        
        print(f"Found {len(participants_data)} participants in backup")
        print(f"Backup created: {backup_info.get('created_at', 'Unknown')}")
        
        # Get database session
        session = next(get_session())
        
        # Clear existing participants for event ID 1
        print("Clearing existing participants for Event ID 1...")
        delete_query = delete(Participant).where(Participant.event_id == 1)
        session.exec(delete_query)
        session.commit()
        
        # Restore participants
        print("Restoring participants...")
        restored_count = 0
        
        for participant_data in participants_data:
            # Remove the original ID to let the database assign new ones
            participant_data_copy = participant_data.copy()
            participant_data_copy.pop('id', None)
            
            # Convert registered_at back to datetime if it exists
            if participant_data_copy.get('registered_at'):
                from datetime import datetime
                participant_data_copy['registered_at'] = datetime.fromisoformat(participant_data_copy['registered_at'])
            
            participant = Participant(**participant_data_copy)
            session.add(participant)
            restored_count += 1
        
        session.commit()
        
        print(f"Restore completed successfully!")
        print(f"Total participants restored: {restored_count}")
        
        # Verify restore
        verify_query = select(Participant).where(Participant.event_id == 1)
        restored_participants = session.exec(verify_query).all()
        print(f"Verification: {len(restored_participants)} participants now in Event ID 1")
        
    except Exception as e:
        print(f"ERROR during restore: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    restore_participants()
