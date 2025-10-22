#!/usr/bin/env python3
"""
Simple winner calculation script for Event ID 1
This calculates winners directly from scorecard data without using the complex WinnerService
"""

from core.database import get_session
from models.event import Event
from models.participant import Participant
from models.scorecard import Scorecard
from models.course import Course, Hole
from sqlmodel import select
from collections import defaultdict

def main():
    session = next(get_session())
    
    # Get event details
    event = session.get(Event, 1)
    if not event:
        print("Event 1 not found!")
        return
    
    print(f"=== WINNER CALCULATION FOR EVENT: {event.name} ===")
    print(f"Scoring Type: {event.scoring_type}")
    print()
    
    # Get all participants and scorecards
    participants = session.exec(select(Participant).where(Participant.event_id == 1)).all()
    scorecards = session.exec(select(Scorecard).where(Scorecard.event_id == 1)).all()
    
    print(f"Total Participants: {len(participants)}")
    print(f"Total Scorecards: {len(scorecards)}")
    
    # Group scorecards by participant
    participant_scores = defaultdict(list)
    for scorecard in scorecards:
        participant_scores[scorecard.participant_id].append(scorecard)
    
    # Calculate totals for each participant
    participant_totals = []
    for participant in participants:
        scores = participant_scores[participant.id]
        if len(scores) == 18:  # Complete round
            total_gross = sum(sc.strokes for sc in scores)
            total_net = sum(sc.net_score for sc in scores)
            total_points = sum(sc.points for sc in scores)
            
            participant_totals.append({
                'participant': participant,
                'gross': total_gross,
                'net': total_net,
                'points': total_points,
                'handicap': participant.declared_handicap,
                'division': participant.division
            })
    
    print(f"Participants with complete scores: {len(participant_totals)}")
    print()
    
    # Sort by gross score (ascending - lower is better)
    participant_totals.sort(key=lambda x: x['gross'])
    
    # Display overall winners (top 10)
    print("OVERALL WINNERS (Top 10) - Sorted by Gross Score")
    print("=" * 80)
    print(f"{'Rank':<4} {'Name':<30} {'Division':<12} {'Gross':<6} {'Net':<6} {'Handicap':<8} {'Points':<6}")
    print("-" * 80)
    
    for rank, data in enumerate(participant_totals[:10], 1):
        participant = data['participant']
        print(f"{rank:<4} {participant.name[:29]:<30} {str(participant.division or 'N/A')[:11]:<12} {data['gross']:<6} {data['net']:<6} {data['handicap']:<8} {data['points']:<6}")
    
    print()
    
    # Sort by net score (ascending - lower is better)
    participant_totals_net = sorted(participant_totals, key=lambda x: x['net'])
    
    print("NET SCORE WINNERS (Top 10) - Sorted by Net Score")
    print("=" * 80)
    print(f"{'Rank':<4} {'Name':<30} {'Division':<12} {'Gross':<6} {'Net':<6} {'Handicap':<8} {'Points':<6}")
    print("-" * 80)
    
    for rank, data in enumerate(participant_totals_net[:10], 1):
        participant = data['participant']
        print(f"{rank:<4} {participant.name[:29]:<30} {str(participant.division or 'N/A')[:11]:<12} {data['gross']:<6} {data['net']:<6} {data['handicap']:<8} {data['points']:<6}")
    
    print()
    
    # Sort by System 36 points (descending - higher is better)
    participant_totals_points = sorted(participant_totals, key=lambda x: x['points'], reverse=True)
    
    print("SYSTEM 36 POINTS LEADERS (Top 10)")
    print("=" * 80)
    print(f"{'Rank':<4} {'Name':<30} {'Division':<12} {'Gross':<6} {'Net':<6} {'Handicap':<8} {'Points':<6}")
    print("-" * 80)
    
    for rank, data in enumerate(participant_totals_points[:10], 1):
        participant = data['participant']
        print(f"{rank:<4} {participant.name[:29]:<30} {str(participant.division or 'N/A')[:11]:<12} {data['gross']:<6} {data['net']:<6} {data['handicap']:<8} {data['points']:<6}")
    
    print()
    
    # Display division winners
    divisions = set(data['division'] for data in participant_totals if data['division'])
    if divisions:
        print("DIVISION WINNERS")
        print("=" * 80)
        
        for division in sorted(divisions):
            division_participants = [data for data in participant_totals if data['division'] == division]
            division_participants.sort(key=lambda x: x['gross'])  # Sort by gross score
            
            print(f"\n{division} Division:")
            print(f"{'Rank':<4} {'Name':<30} {'Gross':<6} {'Net':<6} {'Handicap':<8} {'Points':<6}")
            print("-" * 60)
            
            for rank, data in enumerate(division_participants[:5], 1):  # Top 5 per division
                participant = data['participant']
                print(f"{rank:<4} {participant.name[:29]:<30} {data['gross']:<6} {data['net']:<6} {data['handicap']:<8} {data['points']:<6}")
    
    print()
    
    # Display tournament statistics
    print("TOURNAMENT STATISTICS")
    print("=" * 40)
    
    if participant_totals:
        gross_scores = [data['gross'] for data in participant_totals]
        net_scores = [data['net'] for data in participant_totals]
        points_scores = [data['points'] for data in participant_totals]
        
        print(f"Average Gross Score: {sum(gross_scores) / len(gross_scores):.1f}")
        print(f"Best Gross Score: {min(gross_scores)}")
        print(f"Worst Gross Score: {max(gross_scores)}")
        print()
        print(f"Average Net Score: {sum(net_scores) / len(net_scores):.1f}")
        print(f"Best Net Score: {min(net_scores)}")
        print(f"Worst Net Score: {max(net_scores)}")
        print()
        print(f"Average System 36 Points: {sum(points_scores) / len(points_scores):.1f}")
        print(f"Best System 36 Points: {max(points_scores)}")
        print(f"Worst System 36 Points: {min(points_scores)}")
    
    print()
    print("Winner calculation completed successfully!")
    
    # Show the champion
    if participant_totals:
        champion = participant_totals[0]  # Best gross score
        print(f"\nCHAMPION: {champion['participant'].name}")
        print(f"   Gross Score: {champion['gross']}")
        print(f"   Net Score: {champion['net']}")
        print(f"   System 36 Points: {champion['points']}")
        print(f"   Handicap: {champion['handicap']}")

if __name__ == "__main__":
    main()
