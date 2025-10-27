"""
Fill Event 3 with realistic System 36 scores for testing winner calculation

This script updates all 16 participants with varied scores to test:
- Different point levels (high, medium, low)
- Tie situations (same points, different tie-breakers)
- All three divisions (A, B, C Flights)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select
from core.database import engine
from models.participant import Participant
from models.scorecard import Scorecard
from models.course import Hole

# Realistic System 36 score patterns
# Format: [hole1_strokes, hole2_strokes, ..., hole18_strokes]
# Points: Par or better = 2, Bogey = 1, Double+ = 0

SCORE_PATTERNS = {
    # A Flight - Better players (14-24 points)
    'Player A1': [4, 5, 4, 5, 4, 5, 4, 3, 5, 5, 4, 4, 5, 6, 4, 5, 4, 4],  # 24 points (12 pars, 6 bogeys)
    'Player A2': [5, 6, 4, 5, 5, 6, 4, 4, 6, 5, 5, 5, 6, 6, 5, 5, 5, 5],  # 18 points (6 pars, 12 bogeys)
    'Player A3': [5, 6, 5, 6, 5, 6, 5, 5, 6, 6, 5, 5, 6, 7, 5, 6, 5, 5],  # 18 points (tie with A2)
    'Player A4': [5, 5, 4, 5, 4, 5, 4, 4, 5, 5, 5, 5, 5, 6, 4, 5, 4, 5],  # 20 points (8 pars, 10 bogeys)
    'Player A5': [5, 6, 5, 5, 5, 6, 5, 4, 6, 6, 5, 5, 6, 6, 5, 6, 5, 6],  # 16 points (2 pars, 14 bogeys)
    'Player A6': [4, 5, 4, 5, 5, 5, 4, 4, 5, 5, 5, 5, 5, 6, 5, 5, 5, 5],  # 20 points (tie with A4)

    # B Flight - Average players (8-14 points)
    'Player B1': [6, 6, 5, 6, 5, 6, 5, 5, 6, 6, 6, 6, 6, 7, 5, 6, 5, 6],  # 14 points (14 bogeys, 4 doubles)
    'Player B2': [6, 7, 5, 6, 6, 7, 5, 5, 7, 6, 6, 6, 7, 7, 6, 6, 6, 6],  # 12 points (12 bogeys, 6 doubles)
    'Player B3': [6, 6, 5, 6, 5, 7, 6, 5, 6, 6, 6, 6, 6, 7, 6, 6, 5, 6],  # 12 points (tie with B2)
    'Player B4': [6, 7, 6, 6, 6, 7, 5, 6, 7, 7, 6, 6, 7, 7, 6, 7, 6, 6],  # 10 points (10 bogeys, 8 doubles)
    'Player B5': [6, 6, 6, 6, 6, 6, 6, 5, 6, 6, 6, 6, 7, 7, 6, 6, 6, 6],  # 10 points (tie with B4)

    # C Flight - Higher handicap (4-10 points)
    'Player C1': [7, 7, 6, 7, 6, 7, 6, 6, 7, 7, 7, 7, 7, 8, 6, 7, 6, 7],  # 8 points (8 bogeys, 10 doubles)
    'Player C2': [7, 8, 6, 7, 7, 8, 6, 6, 8, 7, 7, 7, 8, 8, 7, 7, 7, 7],  # 6 points (6 bogeys, 12 doubles)
    'Player C3': [7, 7, 6, 7, 6, 8, 6, 6, 8, 7, 7, 7, 8, 8, 6, 7, 6, 7],  # 6 points (tie with C2)
    'Player C4': [7, 8, 7, 7, 7, 8, 6, 7, 8, 8, 7, 7, 8, 8, 7, 7, 7, 7],  # 4 points (4 bogeys, 14 doubles)
    'Player C5': [8, 8, 7, 8, 7, 8, 7, 7, 8, 8, 8, 8, 8, 9, 7, 8, 7, 8],  # 2 points (2 bogeys, 16 doubles)
}

def fill_scores():
    """Fill event 3 with realistic scores"""

    print("\n" + "="*70)
    print("FILLING EVENT 3 WITH REALISTIC SYSTEM 36 SCORES")
    print("="*70 + "\n")

    with Session(engine) as session:
        # Get all holes for the course
        event_id = 3
        course_id = 1

        holes = session.exec(
            select(Hole).where(Hole.course_id == course_id).order_by(Hole.number)
        ).all()

        if len(holes) != 18:
            print(f"[ERROR] Expected 18 holes, found {len(holes)}")
            return False

        # Get all participants for event 3
        participants = session.exec(
            select(Participant).where(Participant.event_id == event_id)
        ).all()

        print(f"Found {len(participants)} participants")
        print(f"Found {len(holes)} holes\n")

        updates = 0

        for participant in participants:
            if participant.name not in SCORE_PATTERNS:
                print(f"[SKIP] No score pattern for {participant.name}")
                continue

            strokes_pattern = SCORE_PATTERNS[participant.name]

            if len(strokes_pattern) != 18:
                print(f"[ERROR] Invalid pattern for {participant.name}: {len(strokes_pattern)} holes")
                continue

            # Get existing scorecards
            scorecards = session.exec(
                select(Scorecard).where(Scorecard.participant_id == participant.id)
            ).all()

            scorecard_map = {sc.hole_id: sc for sc in scorecards}

            # Update each hole
            for hole_idx, hole in enumerate(holes):
                new_strokes = strokes_pattern[hole_idx]

                if hole.id in scorecard_map:
                    scorecard = scorecard_map[hole.id]
                    scorecard.strokes = new_strokes
                    session.add(scorecard)
                    updates += 1

            print(f"[OK] Updated {participant.name:15} - {participant.division}")

        session.commit()

        print(f"\n[OK] Updated {updates} scorecards")

        # Show summary
        print("\n" + "-"*70)
        print("UPDATED SCORES SUMMARY")
        print("-"*70 + "\n")

        participants = session.exec(
            select(Participant).where(Participant.event_id == event_id)
        ).all()

        for participant in participants:
            scorecards = session.exec(
                select(Scorecard).where(Scorecard.participant_id == participant.id)
            ).all()

            total_strokes = sum(sc.strokes for sc in scorecards if sc.strokes)
            print(f"{participant.name:15} {participant.division:15} Gross: {total_strokes:3} strokes")

        print("\n" + "="*70)
        print("SCORES UPDATED - Run backfill to calculate points!")
        print("="*70 + "\n")

        return True

if __name__ == "__main__":
    success = fill_scores()
    sys.exit(0 if success else 1)
