from sqlmodel import Session, select, func
from typing import Optional, List
from models.event_division import EventDivision
from models.event import Event
from models.participant import Participant
from schemas.event_division import (
    EventDivisionCreate, EventDivisionUpdate, EventDivisionResponse, EventDivisionBulkCreate
)


class EventDivisionService:
    def __init__(self, session: Session):
        self.session = session

    def create_division(self, division_data: EventDivisionCreate) -> EventDivision:
        """Create a new event division"""
        # Verify event exists
        event = self.session.get(Event, division_data.event_id)
        if not event:
            raise ValueError(f"Event with id {division_data.event_id} not found")

        # Check if division name already exists for this event
        existing_division = self.session.exec(
            select(EventDivision).where(
                EventDivision.event_id == division_data.event_id,
                EventDivision.name == division_data.name
            )
        ).first()
        
        if existing_division:
            raise ValueError(f"Division '{division_data.name}' already exists for this event")

        division = EventDivision(**division_data.model_dump())
        self.session.add(division)
        self.session.commit()
        self.session.refresh(division)
        return division

    def create_divisions_bulk(self, bulk_data: EventDivisionBulkCreate) -> List[EventDivision]:
        """Create multiple divisions for an event"""
        # Verify event exists
        event = self.session.get(Event, bulk_data.event_id)
        if not event:
            raise ValueError(f"Event with id {bulk_data.event_id} not found")

        divisions = []
        for division_data in bulk_data.divisions:
            # Check if division name already exists
            existing_division = self.session.exec(
                select(EventDivision).where(
                    EventDivision.event_id == bulk_data.event_id,
                    EventDivision.name == division_data.name
                )
            ).first()
            
            if not existing_division:
                division = EventDivision(
                    event_id=bulk_data.event_id,
                    **division_data.model_dump()
                )
                self.session.add(division)
                divisions.append(division)

        self.session.commit()
        for division in divisions:
            self.session.refresh(division)
        
        return divisions

    def get_division(self, division_id: int) -> Optional[EventDivision]:
        """Get division by ID"""
        return self.session.get(EventDivision, division_id)

    def get_divisions_for_event(self, event_id: int) -> List[EventDivision]:
        """Get all divisions for an event"""
        query = select(EventDivision).where(
            EventDivision.event_id == event_id,
            EventDivision.is_active == True
        ).order_by(EventDivision.name)
        
        divisions = self.session.exec(query).all()
        
        return divisions

    def update_division(self, division_id: int, division_data: EventDivisionUpdate) -> Optional[EventDivision]:
        """Update a division"""
        division = self.session.get(EventDivision, division_id)
        if not division:
            return None

        # Check if new name conflicts with existing divisions
        if division_data.name and division_data.name != division.name:
            existing_division = self.session.exec(
                select(EventDivision).where(
                    EventDivision.event_id == division.event_id,
                    EventDivision.name == division_data.name,
                    EventDivision.id != division_id
                )
            ).first()
            
            if existing_division:
                raise ValueError(f"Division '{division_data.name}' already exists for this event")

        update_data = division_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(division, field, value)
        
        self.session.add(division)
        self.session.commit()
        self.session.refresh(division)
        return division

    def delete_division(self, division_id: int) -> bool:
        """Delete a division (soft delete by setting is_active=False)"""
        division = self.session.get(EventDivision, division_id)
        if not division:
            return False

        # Check if any participants are assigned to this division
        participant_count = self.session.exec(
            select(func.count(Participant.id)).where(
                Participant.division_id == division_id
            )
        ).one()
        
        if participant_count > 0:
            # Soft delete - just deactivate
            division.is_active = False
            self.session.add(division)
        else:
            # Hard delete if no participants
            self.session.delete(division)
        
        self.session.commit()
        return True

    def get_division_stats(self, event_id: int) -> dict:
        """Get division statistics for an event"""
        divisions = self.get_divisions_for_event(event_id)
        
        stats = {
            "total_divisions": len(divisions),
            "active_divisions": len([d for d in divisions if d.is_active]),
            "total_participants": 0,
            "divisions": []
        }
        
        for division in divisions:
            # Get participant count for this division
            participant_count = self.session.exec(
                select(func.count(Participant.id)).where(
                    Participant.division_id == division.id
                )
            ).one()
            
            stats["total_participants"] += participant_count
            
            stats["divisions"].append({
                "id": division.id,
                "name": division.name,
                "participant_count": participant_count,
                "max_participants": division.max_participants,
                "is_full": division.max_participants and participant_count >= division.max_participants
            })
        
        return stats
