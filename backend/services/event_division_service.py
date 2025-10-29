from sqlmodel import Session, select, func
from typing import Optional, List, Dict, Any
from models.event_division import EventDivision, DivisionType
from models.event import Event, ScoringType, System36Variant
from models.participant import Participant
from schemas.event_division import (
    EventDivisionCreate, EventDivisionUpdate, EventDivisionResponse, EventDivisionBulkCreate
)


class EventDivisionService:
    def __init__(self, session: Session):
        self.session = session

    def _apply_smart_defaults(self, event: Event, division_data: dict) -> dict:
        """
        Apply smart defaults for use_course_handicap_for_assignment based on event scoring type.

        HYBRID APPROACH:
        - If user explicitly set the value (True or False), keep it (user override)
        - If not set (None), apply smart default based on rules:
          * System 36 STANDARD + Men divisions → TRUE
          * All other cases → FALSE
        """
        # Only apply default if user hasn't explicitly set it (value is None)
        value = division_data.get('use_course_handicap_for_assignment')

        if value is None:
            # Check if this should use course handicap by default
            should_use_course_hcp = (
                event.scoring_type == ScoringType.SYSTEM_36 and
                event.system36_variant == System36Variant.STANDARD and
                division_data.get('division_type') == DivisionType.MEN
            )

            division_data['use_course_handicap_for_assignment'] = should_use_course_hcp
        # else: user has explicitly set it to True or False, keep their choice

        return division_data

    def create_division(self, division_data: EventDivisionCreate) -> EventDivision:
        """Create a new event division with smart defaults"""
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

        # Apply smart defaults based on event scoring type (HYBRID APPROACH)
        division_dict = division_data.model_dump()
        division_dict = self._apply_smart_defaults(event, division_dict)

        division = EventDivision(**division_dict)
        self.session.add(division)
        self.session.commit()
        self.session.refresh(division)
        return division

    def create_divisions_bulk(self, bulk_data: EventDivisionBulkCreate) -> List[EventDivision]:
        """Create multiple divisions for an event with smart defaults"""
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
                # Apply smart defaults based on event scoring type (HYBRID APPROACH)
                division_dict = division_data.model_dump()
                division_dict['event_id'] = bulk_data.event_id
                division_dict = self._apply_smart_defaults(event, division_dict)

                division = EventDivision(**division_dict)
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

    def create_default_divisions(self, event_id: int) -> List[EventDivision]:
        """
        Create default divisions for an event.

        Creates base divisions: Men, Ladies, Senior, VIP.
        """
        event = self.session.get(Event, event_id)
        if not event:
            raise ValueError(f"Event with id {event_id} not found")

        # Check if divisions already exist
        existing_divisions = self.get_divisions_for_event(event_id)
        if existing_divisions:
            return existing_divisions

        divisions_to_create = [
            EventDivision(
                event_id=event_id,
                name="Men",
                division_type=DivisionType.MEN,
                description="Men's Division"
            ),
            EventDivision(
                event_id=event_id,
                name="Ladies",
                division_type=DivisionType.WOMEN,
                description="Ladies Division"
            ),
            EventDivision(
                event_id=event_id,
                name="Senior",
                division_type=DivisionType.SENIOR,
                description="Senior Division"
            ),
            EventDivision(
                event_id=event_id,
                name="VIP",
                division_type=DivisionType.VIP,
                description="VIP Division"
            )
        ]

        for division in divisions_to_create:
            self.session.add(division)

        self.session.commit()

        # Refresh all divisions to get their IDs
        for division in divisions_to_create:
            self.session.refresh(division)

        return divisions_to_create
