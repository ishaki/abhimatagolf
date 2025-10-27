#!/usr/bin/env python3
"""
Script to restore participants from backup JSON file to Event ID 2
"""
import sys
import os
import json
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select
from core.database import engine
from models.event import Event
from models.event_division import EventDivision
from models.participant import Participant


def restore_participants_to_event2(backup_file_path: str):
    """Restore participants from a JSON backup file to Event ID 2"""

    # Read backup file
    print(f"Reading backup file: {backup_file_path}")
    with open(backup_file_path, 'r', encoding='utf-8') as f:
        backup_data = json.load(f)

    backup_info = backup_data.get('backup_info', {})
    participants_data = backup_data.get('participants', [])

    print(f"Backup info: {backup_info}")
    print(f"Total participants in backup: {len(participants_data)}")

    with Session(engine) as session:
        # Use Event ID 2
        event_id = 2
        event = session.get(Event, event_id)

        if not event:
            print(f"ERROR: Event ID {event_id} not found!")
            return

        print(f"\nUsing event: {event.name} (ID: {event.id})")

        # Get existing divisions for this event
        existing_divisions = session.exec(
            select(EventDivision).where(EventDivision.event_id == event.id)
        ).all()

        division_map = {}  # Maps division name to division ID
        for div in existing_divisions:
            division_map[div.name] = div.id

        # Identify unique divisions from backup
        unique_divisions = set()
        for p in participants_data:
            if p.get('division'):
                unique_divisions.add(p['division'])

        print(f"\nUnique divisions found in backup: {unique_divisions}")
        print(f"Existing divisions in event: {[d.name for d in existing_divisions]}")

        # Create missing divisions
        for div_name in unique_divisions:
            if div_name not in division_map:
                print(f"Creating division: {div_name}")

                # Determine handicap range based on division name
                if 'A' in div_name:
                    min_hcp, max_hcp = 0, 12
                elif 'B' in div_name:
                    min_hcp, max_hcp = 13, 18
                elif 'C' in div_name:
                    min_hcp, max_hcp = 19, 24
                elif 'LADIES' in div_name.upper():
                    min_hcp, max_hcp = 0, 36
                elif 'SENIOR' in div_name.upper():
                    min_hcp, max_hcp = 0, 36
                else:
                    min_hcp, max_hcp = 0, 36

                # Determine division type based on division name
                division_type = None
                if 'MEN' in div_name.upper() or 'A' in div_name or 'B' in div_name or 'C' in div_name:
                    division_type = "men"
                elif 'LADIES' in div_name.upper() or 'WOMEN' in div_name.upper():
                    division_type = "women"
                elif 'SENIOR' in div_name.upper():
                    division_type = "senior"
                elif 'VIP' in div_name.upper():
                    division_type = "vip"
                else:
                    division_type = "mixed"

                new_division = EventDivision(
                    event_id=event.id,
                    name=div_name,
                    division_type=division_type,
                    handicap_min=min_hcp,
                    handicap_max=max_hcp
                )
                session.add(new_division)
                session.flush()
                division_map[div_name] = new_division.id
                print(f"  Created division ID: {new_division.id}")

        session.commit()

        # Delete existing participants for this event (if any)
        print(f"\nDeleting existing participants for event {event.id}...")
        existing_participants = session.exec(
            select(Participant).where(Participant.event_id == event.id)
        ).all()
        for p in existing_participants:
            session.delete(p)
        session.commit()
        print(f"Deleted {len(existing_participants)} existing participants")

        # Restore participants
        print(f"\nRestoring participants to Event ID {event_id}...")
        restored_count = 0
        skipped_count = 0

        for p_data in participants_data:
            try:
                # Determine division_id
                division_id = None
                if p_data.get('division') and p_data['division'] in division_map:
                    division_id = division_map[p_data['division']]

                # Create participant
                participant = Participant(
                    event_id=event.id,
                    name=p_data['name'],
                    declared_handicap=p_data.get('declared_handicap', 0.0),
                    division_id=division_id,
                    country=p_data.get('country'),
                    sex=p_data.get('sex'),
                    phone_no=p_data.get('phone_no'),
                    event_status=p_data.get('event_status', 'Ok'),
                    event_description=p_data.get('event_description')
                )
                session.add(participant)
                restored_count += 1

                if restored_count % 10 == 0:
                    print(f"  Restored {restored_count} participants...")

            except Exception as e:
                print(f"  ERROR restoring participant {p_data.get('name')}: {e}")
                skipped_count += 1

        session.commit()

        print(f"\n{'='*60}")
        print(f"Restoration complete!")
        print(f"  Event ID: {event.id}")
        print(f"  Event Name: {event.name}")
        print(f"  Divisions created/used: {len(division_map)}")
        print(f"  Participants restored: {restored_count}")
        print(f"  Participants skipped: {skipped_count}")
        print(f"{'='*60}")

        # Show division summary
        print(f"\nDivision Summary:")
        for div_name, div_id in division_map.items():
            count = session.exec(
                select(Participant)
                .where(Participant.event_id == event.id)
                .where(Participant.division_id == div_id)
            ).all()
            print(f"  {div_name}: {len(count)} participants")

        # Show unassigned
        unassigned = session.exec(
            select(Participant)
            .where(Participant.event_id == event.id)
            .where(Participant.division_id == None)
        ).all()
        print(f"  Unassigned: {len(unassigned)} participants")


if __name__ == "__main__":
    # Default backup file path
    backup_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'Utils',
        'backup_participants_event1.json'
    )

    # Check if file exists
    if not os.path.exists(backup_file):
        print(f"ERROR: Backup file not found at {backup_file}")
        sys.exit(1)

    print(f"Starting participant restoration to Event ID 2")
    print(f"From: {backup_file}")
    print(f"{'='*60}\n")

    restore_participants_to_event2(backup_file)
