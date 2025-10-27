"""
Reassign participants to correct divisions based on course handicap

For System 36 STANDARD events with Men divisions:
- Participants should be assigned to divisions based on course_handicap
- Not declared_handicap

This script:
1. Finds divisions with use_course_handicap_for_assignment = True
2. Reassigns participants based on their course_handicap
3. Updates participant.division and participant.division_id
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select
from core.database import engine
from models.event import Event, ScoringType, System36Variant
from models.event_division import EventDivision
from models.participant import Participant

def reassign_participants(event_id: int = None):
    """Reassign participants based on course handicap"""

    print("\n" + "="*90)
    print("REASSIGN PARTICIPANTS BY COURSE HANDICAP")
    print("="*90 + "\n")

    with Session(engine) as session:
        # Get events to process
        if event_id:
            event = session.get(Event, event_id)
            if not event:
                print(f"[ERROR] Event {event_id} not found")
                return False
            events = [event]
        else:
            # Get all System 36 STANDARD events
            events = session.exec(
                select(Event).where(
                    Event.scoring_type == ScoringType.SYSTEM_36,
                    Event.system36_variant == System36Variant.STANDARD
                )
            ).all()

        if not events:
            print("[INFO] No events to process")
            return True

        total_reassigned = 0

        for event in events:
            print(f"Event: {event.name} (ID: {event.id})")
            print("-" * 90)

            # Get divisions that use course handicap
            divisions = session.exec(
                select(EventDivision).where(
                    EventDivision.event_id == event.id,
                    EventDivision.use_course_handicap_for_assignment == True
                )
            ).all()

            if not divisions:
                print(f"[SKIP] No divisions use course handicap for assignment\n")
                continue

            # Sort divisions by handicap_min for proper matching
            divisions = sorted(divisions, key=lambda d: d.handicap_min or 0)

            # Get all participants for this event
            participants = session.exec(
                select(Participant).where(Participant.event_id == event.id)
            ).all()

            if not participants:
                print(f"[SKIP] No participants found\n")
                continue

            print(f"\nReassigning {len(participants)} participant(s)...\n")
            print(f"{'Name':<15} {'Old Division':<20} {'Course HCP':<12} {'New Division':<20}")
            print("-" * 90)

            for participant in participants:
                course_hcp = participant.course_handicap
                old_division = participant.division or "None"

                # Find correct division based on course handicap
                new_division = None
                for division in divisions:
                    if division.handicap_min is not None and division.handicap_max is not None:
                        if division.handicap_min <= course_hcp <= division.handicap_max:
                            new_division = division
                            break

                if new_division:
                    # Only update if changed
                    if participant.division_id != new_division.id:
                        participant.division_id = new_division.id
                        participant.division = new_division.name
                        session.add(participant)
                        total_reassigned += 1
                        print(f"{participant.name:<15} {old_division:<20} {course_hcp:<12} {new_division.name:<20} [UPDATED]")
                    else:
                        print(f"{participant.name:<15} {old_division:<20} {course_hcp:<12} {new_division.name:<20} [OK]")
                else:
                    print(f"{participant.name:<15} {old_division:<20} {course_hcp:<12} {'NO MATCH':<20} [ERROR]")

            print()

        # Commit changes
        if total_reassigned > 0:
            session.commit()
            print("\n" + "="*90)
            print(f"SUMMARY: Reassigned {total_reassigned} participant(s)")
            print("="*90 + "\n")
        else:
            print("\n" + "="*90)
            print("SUMMARY: No participants needed reassignment")
            print("="*90 + "\n")

        return True

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Reassign participants by course handicap')
    parser.add_argument('--event-id', type=int, help='Specific event ID to process')
    args = parser.parse_args()

    success = reassign_participants(event_id=args.event_id)
    sys.exit(0 if success else 1)
