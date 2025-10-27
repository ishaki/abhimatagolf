#!/usr/bin/env python3
"""
Script to verify participant restoration
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select
from core.database import engine
from models.participant import Participant
from models.event_division import EventDivision

with Session(engine) as session:
    # Get all participants for event 1
    participants = session.exec(
        select(Participant).where(Participant.event_id == 1)
    ).all()

    # Get all divisions for event 1
    divisions = session.exec(
        select(EventDivision).where(EventDivision.event_id == 1)
    ).all()

    print("\n" + "="*60)
    print("PARTICIPANT RESTORATION VERIFICATION")
    print("="*60)
    print(f"Total Participants: {len(participants)}")
    print(f"Total Divisions: {len(divisions)}")

    print(f"\nDivisions:")
    for d in divisions:
        print(f"  - {d.name} (ID: {d.id})")

    # Count participants by division
    div_counts = {}
    for p in participants:
        if p.division_id:
            div_name = next((d.name for d in divisions if d.id == p.division_id), 'Unknown')
        else:
            div_name = 'Unassigned'
        div_counts[div_name] = div_counts.get(div_name, 0) + 1

    print(f"\nParticipants by Division:")
    for div, count in sorted(div_counts.items()):
        print(f"  {div}: {count} participants")

    # Show sample participants
    print(f"\nSample Participants (first 10):")
    for i, p in enumerate(participants[:10]):
        div_name = next((d.name for d in divisions if d.id == p.division_id), 'Unassigned') if p.division_id else 'Unassigned'
        print(f"  {i+1}. {p.name} - HCP: {p.declared_handicap} - Division: {div_name}")

    print("="*60 + "\n")
