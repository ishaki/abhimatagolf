#!/usr/bin/env python3
"""
Script to verify Event ID 2 participants
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select
from core.database import engine
from models.participant import Participant
from models.event_division import EventDivision
from models.event import Event

EVENT_ID = 2

with Session(engine) as session:
    # Get event
    event = session.get(Event, EVENT_ID)

    if not event:
        print(f"ERROR: Event ID {EVENT_ID} not found!")
        sys.exit(1)

    # Get all participants for event
    participants = session.exec(
        select(Participant).where(Participant.event_id == EVENT_ID)
    ).all()

    # Get all divisions for event
    divisions = session.exec(
        select(EventDivision).where(EventDivision.event_id == EVENT_ID)
    ).all()

    print("\n" + "="*70)
    print(f"EVENT: {event.name} (ID: {EVENT_ID})")
    print("="*70)
    print(f"Description: {event.description}")
    print(f"Date: {event.event_date}")
    print(f"Scoring Type: {event.scoring_type}")
    print(f"Total Participants: {len(participants)}")
    print(f"Total Divisions: {len(divisions)}")

    print(f"\n{'='*70}")
    print("DIVISIONS")
    print("="*70)
    for d in divisions:
        count = len([p for p in participants if p.division_id == d.id])
        print(f"{d.name:25} - Participants: {count:3}")

    # Count participants by division
    div_counts = {}
    for p in participants:
        if p.division_id:
            div_name = next((d.name for d in divisions if d.id == p.division_id), 'Unknown')
        else:
            div_name = 'Unassigned'
        div_counts[div_name] = div_counts.get(div_name, 0) + 1

    print(f"\n{'='*70}")
    print("PARTICIPANTS BY DIVISION")
    print("="*70)
    for div, count in sorted(div_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"{div:25} : {count:3} participants")

    # Show sample participants
    print(f"\n{'='*70}")
    print("SAMPLE PARTICIPANTS (First 20)")
    print("="*70)
    print(f"{'No.':<5} {'Name':<35} {'HCP':<6} {'Division':<20}")
    print("-" * 70)
    for i, p in enumerate(participants[:20]):
        div_name = next((d.name for d in divisions if d.id == p.division_id), 'Unassigned') if p.division_id else 'Unassigned'
        print(f"{i+1:<5} {p.name:<35} {p.declared_handicap:<6.1f} {div_name:<20}")

    print("\n" + "="*70 + "\n")
