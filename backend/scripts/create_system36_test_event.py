#!/usr/bin/env python3
"""
Script to create a System 36 test event with divisions and participants
"""
import sys
import os
from datetime import datetime, timedelta
import random

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select
from core.database import engine
from models.user import User
from models.course import Course, Hole
from models.event import Event, ScoringType
from models.event_division import EventDivision
from models.participant import Participant
from models.scorecard import Scorecard

def create_system36_test_event():
    """Create ILUNI TEST event with System 36 scoring"""

    print("\n" + "="*70)
    print("CREATING SYSTEM 36 TEST EVENT")
    print("="*70)

    with Session(engine) as session:
        # Get first available user and course
        user = session.exec(select(User)).first()
        course = session.exec(select(Course)).first()

        if not user or not course:
            print("ERROR: No user or course found in database!")
            return False

        print(f"\nUsing User: {user.full_name} (ID: {user.id})")
        print(f"Using Course: {course.name} (ID: {course.id})")

        # Check if event already exists
        existing = session.exec(
            select(Event).where(Event.name == "ILUNI TEST")
        ).first()

        if existing:
            print(f"\nEvent 'ILUNI TEST' already exists (ID: {existing.id})")
            print("Deleting old event...")
            session.delete(existing)
            session.commit()

        # Create event
        print("\n[1/4] Creating Event...")
        event = Event(
            name="ILUNI TEST",
            course_id=course.id,
            event_date=datetime.now().date() + timedelta(days=1),
            scoring_type=ScoringType.SYSTEM_36,
            system36_variant="standard",
            max_participants=16,
            created_by=user.id
        )
        session.add(event)
        session.commit()
        session.refresh(event)
        print(f"[OK] Event created: {event.name} (ID: {event.id})")
        print(f"  Scoring Type: {event.scoring_type}")

        # Create divisions
        print("\n[2/4] Creating Divisions...")
        divisions_data = [
            {"name": "MEN-A", "division_type": "men", "handicap_min": 1, "handicap_max": 12, "max_participants": 6, "use_course_handicap_for_assignment": True},
            {"name": "MEN-B", "division_type": "men", "handicap_min": 13, "handicap_max": 18, "max_participants": 5, "use_course_handicap_for_assignment": True},
            {"name": "MEN-C", "division_type": "men", "handicap_min": 19, "handicap_max": 26, "max_participants": 5, "use_course_handicap_for_assignment": True},
        ]

        divisions = {}
        for div_data in divisions_data:
            division = EventDivision(
                event_id=event.id,
                **div_data
            )
            session.add(division)
            session.commit()
            session.refresh(division)
            divisions[div_data["name"]] = division
            print(f"[OK] Division: {division.name} (HCP {division.handicap_min}-{division.handicap_max})")

        # Create 16 participants with varied handicaps
        print("\n[3/4] Creating 16 Participants...")
        participants_data = [
            # Men A (1-12) - 6 players
            {"name": "Player A1", "handicap": 5, "division": "MEN-A"},
            {"name": "Player A2", "handicap": 8, "division": "MEN-A"},
            {"name": "Player A3", "handicap": 10, "division": "MEN-A"},
            {"name": "Player A4", "handicap": 3, "division": "MEN-A"},
            {"name": "Player A5", "handicap": 12, "division": "MEN-A"},
            {"name": "Player A6", "handicap": 6, "division": "MEN-A"},
            # Men B (13-18) - 5 players
            {"name": "Player B1", "handicap": 14, "division": "MEN-B"},
            {"name": "Player B2", "handicap": 16, "division": "MEN-B"},
            {"name": "Player B3", "handicap": 18, "division": "MEN-B"},
            {"name": "Player B4", "handicap": 13, "division": "MEN-B"},
            {"name": "Player B5", "handicap": 17, "division": "MEN-B"},
            # Men C (19-26) - 5 players
            {"name": "Player C1", "handicap": 20, "division": "MEN-C"},
            {"name": "Player C2", "handicap": 22, "division": "MEN-C"},
            {"name": "Player C3", "handicap": 24, "division": "MEN-C"},
            {"name": "Player C4", "handicap": 19, "division": "MEN-C"},
            {"name": "Player C5", "handicap": 26, "division": "MEN-C"},
        ]

        participants = []
        for p_data in participants_data:
            participant = Participant(
                event_id=event.id,
                name=p_data["name"],
                declared_handicap=p_data["handicap"],
                division_id=divisions[p_data["division"]].id
            )
            session.add(participant)
            participants.append(participant)

        session.commit()
        for p in participants:
            session.refresh(p)

        print(f"[OK] Created {len(participants)} participants")
        for p in participants:
            div_name = next((d["division"] for d in participants_data if d["name"] == p.name))
            print(f"  - {p.name} (HCP {p.declared_handicap}, {div_name})")

        # Fill in scores
        print("\n[4/4] Filling Scores for All Participants...")

        # Get all holes for the course
        holes = session.exec(
            select(Hole).where(Hole.course_id == course.id).order_by(Hole.number)
        ).all()

        if len(holes) != 18:
            print(f"WARNING: Course has {len(holes)} holes, expected 18")
            return False

        # Generate realistic scores for each participant
        for participant in participants:
            print(f"\n  Scoring for {participant.name} (HCP {participant.declared_handicap})...")
            total_strokes = 0
            total_points = 0

            for hole in holes:
                # Generate realistic score based on handicap
                # Better players shoot closer to par
                base_score = hole.par

                # Add variation based on handicap
                if participant.declared_handicap <= 10:
                    # Low handicap: mostly pars and bogeys, occasional birdie
                    variation = random.choices([0, 1, 2, -1], weights=[40, 40, 15, 5])[0]
                elif participant.declared_handicap <= 18:
                    # Mid handicap: mostly bogeys and pars
                    variation = random.choices([0, 1, 2, 3], weights=[30, 45, 20, 5])[0]
                else:
                    # High handicap: bogeys and doubles
                    variation = random.choices([1, 2, 3], weights=[40, 45, 15])[0]

                strokes = base_score + variation

                # Calculate System 36 points (GROSS scoring)
                score_to_par = strokes - hole.par
                if score_to_par <= 0:  # Par or better
                    points = 2
                elif score_to_par == 1:  # Bogey
                    points = 1
                else:  # Double or worse
                    points = 0

                # Create scorecard
                scorecard = Scorecard(
                    participant_id=participant.id,
                    event_id=event.id,
                    hole_id=hole.id,
                    strokes=strokes,
                    points=points,
                    recorded_by=user.id
                )
                session.add(scorecard)

                total_strokes += strokes
                total_points += points

            session.commit()

            # Calculate System 36 handicap
            system36_hcp = 36 - total_points
            net_score = total_strokes - system36_hcp

            print(f"    [OK] Gross: {total_strokes}, Points: {total_points}, "
                  f"S36 HCP: {system36_hcp}, Net: {net_score}")

        print("\n" + "="*70)
        print("[SUCCESS] SYSTEM 36 TEST EVENT CREATED SUCCESSFULLY!")
        print("="*70)
        print(f"\nEvent ID: {event.id}")
        print(f"Event Name: {event.name}")
        print(f"Scoring Type: {event.scoring_type}")
        print(f"Total Participants: {len(participants)}")
        print(f"Total Divisions: {len(divisions)}")
        print("\nDivisions:")
        for div_name, div in divisions.items():
            count = len([p for p in participants if p.division_id == div.id])
            print(f"  - {div_name}: {count} players (HCP {div.handicap_min}-{div.handicap_max})")

        print("\n" + "="*70 + "\n")
        return True


if __name__ == "__main__":
    success = create_system36_test_event()
    sys.exit(0 if success else 1)
