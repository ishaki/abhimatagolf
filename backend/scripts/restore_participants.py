#!/usr/bin/env python3
"""
Script to restore participants from backup JSON file
"""
import sys
import os
import json
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select
from core.database import engine
from models.event import Event, ScoringType
from models.event_division import EventDivision
from models.participant import Participant
from models.course import Course
from models.user import User


def restore_participants_from_backup(backup_file_path: str):
    """Restore participants from a JSON backup file"""

    # Read backup file
    print(f"Reading backup file: {backup_file_path}")
    with open(backup_file_path, 'r', encoding='utf-8') as f:
        backup_data = json.load(f)

    backup_info = backup_data.get('backup_info', {})
    participants_data = backup_data.get('participants', [])

    print(f"Backup info: {backup_info}")
    print(f"Total participants in backup: {len(participants_data)}")

    with Session(engine) as session:
        # Check if event exists, create if not
        event_id = backup_info.get('event_id', 1)
        event = session.get(Event, event_id)

        if not event:
            print(f"Event ID {event_id} not found. Creating new event...")

            # Get first course
            course = session.exec(select(Course)).first()
            if not course:
                print("ERROR: No course found in database. Please create a course first.")
                return

            # Get admin user
            admin_user = session.exec(select(User)).first()
            if not admin_user:
                print("ERROR: No user found in database. Please create a user first.")
                return

            # Create event
            event = Event(
                name="Restored Event from Backup",
                description="Event restored from backup file",
                course_id=course.id,
                event_date=datetime.utcnow(),
                scoring_type=ScoringType.NET_STROKE,
                system36_variant="standard",
                created_by=admin_user.id
            )
            session.add(event)
            session.flush()
            print(f"Created event with ID: {event.id}")
        else:
            print(f"Using existing event: {event.name} (ID: {event.id})")

        # Get or create divisions
        division_map = {}  # Maps division name to division ID

        # Get existing divisions for this event
        existing_divisions = session.exec(
            select(EventDivision).where(EventDivision.event_id == event.id)
        ).all()

        for div in existing_divisions:
            division_map[div.name] = div.id

        # Identify unique divisions from backup
        unique_divisions = set()
        for p in participants_data:
            if p.get('division'):
                unique_divisions.add(p['division'])

        print(f"\nUnique divisions found in backup: {unique_divisions}")

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

                new_division = EventDivision(
                    event_id=event.id,
                    name=div_name,
                    min_handicap=min_hcp,
                    max_handicap=max_hcp
                )
                session.add(new_division)
                session.flush()
                division_map[div_name] = new_division.id
                print(f"  Created division ID: {new_division.id}")

        session.commit()

        # Delete existing participants for this event (optional - comment out if you want to keep existing)
        print(f"\nDeleting existing participants for event {event.id}...")
        existing_participants = session.exec(
            select(Participant).where(Participant.event_id == event.id)
        ).all()
        for p in existing_participants:
            session.delete(p)
        session.commit()
        print(f"Deleted {len(existing_participants)} existing participants")

        # Restore participants
        print(f"\nRestoring participants...")
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

    # Allow custom backup file path as argument
    if len(sys.argv) > 1:
        backup_file = sys.argv[1]

    print(f"Starting participant restoration from: {backup_file}")
    print(f"{'='*60}\n")

    restore_participants_from_backup(backup_file)
