#!/usr/bin/env python3
"""
Backup Participants from Event ID 1
==================================

This script backs up all participants from event ID 1 to a JSON file
that can be used later to restore the participants for testing purposes.

Usage:
    python backup_participants_event1.py

The script will create:
- backup_participants_event1.json: Contains all participant data
- restore_participants_event1.py: Script to restore the participants
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add the backend directory to the Python path
sys.path.append(str(Path(__file__).parent))

from core.database import get_session
from models.participant import Participant
from sqlmodel import select


def backup_participants():
    """Backup all participants from event ID 1"""
    
    print("Starting backup of participants from Event ID 1...")
    
    try:
        # Get database session
        session = next(get_session())
        
        # Fetch all participants from event ID 1
        participants_query = select(Participant).where(Participant.event_id == 1)
        participants = session.exec(participants_query).all()
        
        print(f"Found {len(participants)} participants in Event ID 1")
        
        if not participants:
            print("WARNING: No participants found in Event ID 1")
            return
        
        # Convert participants to dictionary format
        participants_data = []
        for participant in participants:
            participant_dict = {
                "id": participant.id,
                "event_id": participant.event_id,
                "name": participant.name,
                "declared_handicap": participant.declared_handicap,
                "division": participant.division,
                "division_id": participant.division_id,
                "registered_at": participant.registered_at.isoformat() if participant.registered_at else None,
                "country": participant.country,
                "sex": participant.sex,
                "phone_no": participant.phone_no,
                "event_status": participant.event_status,
                "event_description": participant.event_description,
            }
            participants_data.append(participant_dict)
        
        # Create backup data structure
        backup_data = {
            "backup_info": {
                "created_at": datetime.now().isoformat(),
                "event_id": 1,
                "total_participants": len(participants_data),
                "description": "Backup of participants from Event ID 1 for testing purposes"
            },
            "participants": participants_data
        }
        
        # Save to JSON file
        backup_file = Path("backup_participants_event1.json")
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)
        
        print(f"Backup completed successfully!")
        print(f"Backup saved to: {backup_file.absolute()}")
        print(f"Total participants backed up: {len(participants_data)}")
        
        # Show sample of backed up data
        if participants_data:
            print("\nSample participant data:")
            sample = participants_data[0]
            print(f"   Name: {sample['name']}")
            print(f"   Handicap: {sample['declared_handicap']}")
            print(f"   Division: {sample['division']}")
            print(f"   Status: {sample['event_status']}")
        
        return backup_file
        
    except Exception as e:
        print(f"ERROR during backup: {str(e)}")
        raise
    finally:
        session.close()


def create_restore_script():
    """Create a restore script for the participants"""
    
    restore_script_content = '''#!/usr/bin/env python3
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
'''
    
    restore_file = Path("restore_participants_event1.py")
    with open(restore_file, 'w', encoding='utf-8') as f:
        f.write(restore_script_content)
    
    print(f"Restore script created: {restore_file.absolute()}")
    return restore_file


if __name__ == "__main__":
    try:
        # Create backup
        backup_file = backup_participants()
        
        # Create restore script
        restore_file = create_restore_script()
        
        print("\nBackup process completed!")
        print(f"Backup file: {backup_file}")
        print(f"Restore script: {restore_file}")
        print("\nTo restore participants later, run:")
        print(f"   python {restore_file}")
        
    except Exception as e:
        print(f"Backup failed: {str(e)}")
        sys.exit(1)
