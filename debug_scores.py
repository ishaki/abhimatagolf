#!/usr/bin/env python3
"""
Debug script to understand score_to_par calculation issue
"""
from core.database import get_session
from models.scorecard import Scorecard
from models.course import Hole
from models.participant import Participant
from sqlmodel import select, and_

def debug_score_calculation():
    session = next(get_session())
    
    print("Debugging score_to_par calculation...")
    print("=" * 50)
    
    # Get first participant with scores
    participants = session.exec(select(Participant)).all()
    print(f"Total participants: {len(participants)}")
    
    for participant in participants[:3]:  # Check first 3 participants
        print(f"\nParticipant {participant.id}: {participant.name}")
        
        # Get scores for this participant
        scores = session.exec(select(Scorecard).where(
            and_(
                Scorecard.participant_id == participant.id,
                Scorecard.strokes > 0
            )
        )).all()
        
        if not scores:
            print("  No scores")
            continue
            
        print(f"  Scores: {len(scores)}")
        
        # Calculate gross score
        gross_score = sum(score.strokes for score in scores)
        print(f"  Gross score: {gross_score} (type: {type(gross_score)})")
        
        # Get course par
        holes = session.exec(select(Hole).where(Hole.course_id == 1)).all()
        course_par = sum(hole.par for hole in holes)
        print(f"  Course par: {course_par} (type: {type(course_par)})")
        
        # Calculate score to par
        score_to_par_raw = gross_score - course_par
        score_to_par_int = int(score_to_par_raw)
        
        print(f"  Score to par (raw): {score_to_par_raw} (type: {type(score_to_par_raw)})")
        print(f"  Score to par (int): {score_to_par_int} (type: {type(score_to_par_int)})")
        
        # Check individual score values
        print("  Individual scores:")
        for score in scores[:5]:  # Show first 5 scores
            print(f"    Hole {score.hole_id}: {score.strokes} strokes (type: {type(score.strokes)})")
        
        # Check hole par values
        print("  Hole pars:")
        for hole in holes[:5]:  # Show first 5 holes
            print(f"    Hole {hole.number}: par {hole.par} (type: {type(hole.par)})")

if __name__ == "__main__":
    debug_score_calculation()
