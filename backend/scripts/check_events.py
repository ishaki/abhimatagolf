#!/usr/bin/env python3
"""
Script to check existing events in database
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select
from core.database import engine
from models.event import Event
from models.participant import Participant
from models.event_division import EventDivision

with Session(engine) as session:
    # Get all events
    events = session.exec(select(Event)).all()

    print("\n" + "="*60)
    print("EVENTS IN DATABASE")
    print("="*60)

    if not events:
        print("No events found in database!")
    else:
        for e in events:
            # Count participants
            p_count = len(session.exec(
                select(Participant).where(Participant.event_id == e.id)
            ).all())

            # Count divisions
            d_count = len(session.exec(
                select(EventDivision).where(EventDivision.event_id == e.id)
            ).all())

            print(f"\nEvent ID: {e.id}")
            print(f"  Name: {e.name}")
            print(f"  Description: {e.description}")
            print(f"  Date: {e.event_date}")
            print(f"  Scoring Type: {e.scoring_type}")
            if hasattr(e, 'system36_variant') and e.system36_variant:
                print(f"  System 36 Variant: {e.system36_variant}")
            print(f"  Participants: {p_count}")
            print(f"  Divisions: {d_count}")
            print(f"  Active: {e.is_active}")

    print("\n" + "="*60 + "\n")
