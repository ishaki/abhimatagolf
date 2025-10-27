"""
Fix System 36 STANDARD divisions to use course handicap for Men divisions

For System 36 STANDARD variant:
- Men divisions should use course_handicap for division assignment
- Women/Other divisions should use declared_handicap

This script:
1. Identifies System 36 STANDARD events
2. Updates Men divisions to set use_course_handicap_for_assignment = True
3. Sets division_type to MEN for Men divisions
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select
from core.database import engine
from models.event import Event, ScoringType, System36Variant
from models.event_division import EventDivision, DivisionType

def fix_system36_divisions():
    """Fix divisions for System 36 STANDARD events"""

    print("\n" + "="*80)
    print("FIX: System 36 STANDARD Division Configuration")
    print("="*80 + "\n")

    with Session(engine) as session:
        # Get all System 36 STANDARD events
        events = session.exec(
            select(Event).where(
                Event.scoring_type == ScoringType.SYSTEM_36,
                Event.system36_variant == System36Variant.STANDARD
            )
        ).all()

        if not events:
            print("[INFO] No System 36 STANDARD events found")
            return True

        print(f"Found {len(events)} System 36 STANDARD event(s)\n")

        total_updated = 0

        for event in events:
            print(f"Event: {event.name} (ID: {event.id})")
            print("-" * 80)

            # Get divisions for this event
            divisions = session.exec(
                select(EventDivision).where(EventDivision.event_id == event.id)
            ).all()

            if not divisions:
                print(f"[SKIP] No divisions found for event {event.id}\n")
                continue

            for division in divisions:
                # Check if this is a Men's division by name
                is_men_division = any(keyword in division.name.lower()
                                     for keyword in ['men', 'man', 'male', 'pria', 'putra'])

                # Skip women's divisions
                is_women_division = any(keyword in division.name.lower()
                                       for keyword in ['women', 'woman', 'ladies', 'lady', 'female', 'wanita', 'putri'])

                if is_women_division:
                    print(f"  [SKIP] {division.name} - Women's division (uses declared handicap)")
                    continue

                if is_men_division:
                    # Update Men's division
                    updated = False

                    # Set division type if not set
                    if division.division_type != DivisionType.MEN:
                        division.division_type = DivisionType.MEN
                        updated = True

                    # Set use_course_handicap_for_assignment to True
                    if not division.use_course_handicap_for_assignment:
                        division.use_course_handicap_for_assignment = True
                        updated = True

                    if updated:
                        session.add(division)
                        print(f"  [UPDATE] {division.name} - Set to use COURSE handicap for assignment")
                        total_updated += 1
                    else:
                        print(f"  [OK] {division.name} - Already configured correctly")
                else:
                    print(f"  [SKIP] {division.name} - Not identified as Men's division")

            print()

        # Commit changes
        session.commit()

        print("="*80)
        print(f"SUMMARY: Updated {total_updated} division(s)")
        print("="*80 + "\n")

        # Show updated configuration
        print("Updated Division Configuration:")
        print("-" * 80)

        for event in events:
            divisions = session.exec(
                select(EventDivision).where(EventDivision.event_id == event.id)
            ).all()

            print(f"\nEvent: {event.name}")
            for div in divisions:
                hcp_type = "COURSE" if div.use_course_handicap_for_assignment else "DECLARED"
                div_type = div.division_type or "N/A"
                print(f"  {div.name:<25} Type: {div_type:<10} Uses: {hcp_type} handicap")

        print("\n" + "="*80)
        print("FIX COMPLETED")
        print("="*80 + "\n")

        return True

if __name__ == "__main__":
    success = fix_system36_divisions()
    sys.exit(0 if success else 1)
