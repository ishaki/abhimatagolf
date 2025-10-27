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

    # ==================== SUB-DIVISION SUPPORT ====================

    def create_default_divisions(self, event_id: int) -> List[EventDivision]:
        """
        Create default divisions based on event scoring type and system36 variant.

        Rules:
        - Stroke Play: Base divisions only (Men, Ladies, Senior, VIP)
        - Net Stroke: Base + pre-defined sub-divisions for Men (A/B/C)
        - System 36 Standard: Base divisions only (sub-divisions created at winner calculation)
        - System 36 Modified: Base + pre-defined sub-divisions for Men (A/B/C)
        - Stableford: Base divisions only (sub-divisions created at winner calculation)
        """
        event = self.session.get(Event, event_id)
        if not event:
            raise ValueError(f"Event with id {event_id} not found")

        # Check if divisions already exist
        existing_divisions = self.get_divisions_for_event(event_id)
        if existing_divisions:
            return existing_divisions

        divisions_to_create = []

        # Determine if we need pre-defined sub-divisions
        needs_predefined_subdivisions = (
            event.scoring_type == ScoringType.NET_STROKE or
            (event.scoring_type == ScoringType.SYSTEM_36 and
             event.system36_variant == System36Variant.MODIFIED)
        )

        # Create Men division (with sub-divisions if needed)
        if needs_predefined_subdivisions:
            # Create parent Men division
            men_parent = EventDivision(
                event_id=event_id,
                name="Men",
                division_type=DivisionType.MEN,
                description="Men's Division (Parent)"
            )
            self.session.add(men_parent)
            self.session.flush()  # Get the ID
            divisions_to_create.append(men_parent)

            # Note: Sub-divisions will be created by event admin with custom handicap ranges
            # We don't create them here as per requirement "Admin defines at event creation"
        else:
            # Create simple Men division
            men_division = EventDivision(
                event_id=event_id,
                name="Men",
                division_type=DivisionType.MEN,
                description="Men's Division"
            )
            divisions_to_create.append(men_division)

        # Create other base divisions (Ladies, Senior, VIP)
        other_divisions = [
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

        for division in other_divisions:
            self.session.add(division)
            divisions_to_create.append(division)

        self.session.commit()

        # Refresh all divisions to get their IDs
        for division in divisions_to_create:
            self.session.refresh(division)

        return divisions_to_create

    def create_subdivision(
        self,
        parent_division_id: int,
        name: str,
        handicap_min: Optional[float] = None,
        handicap_max: Optional[float] = None,
        description: Optional[str] = None
    ) -> EventDivision:
        """
        Create a sub-division under a parent division.

        Args:
            parent_division_id: ID of the parent division
            name: Name of the sub-division (e.g., "Men A", "Men B", "Men C")
            handicap_min: Minimum handicap for this sub-division
            handicap_max: Maximum handicap for this sub-division
            description: Optional description
        """
        # Verify parent division exists
        parent_division = self.session.get(EventDivision, parent_division_id)
        if not parent_division:
            raise ValueError(f"Parent division with id {parent_division_id} not found")

        # Verify parent division doesn't already have a parent (no nested sub-divisions)
        if parent_division.parent_division_id is not None:
            raise ValueError("Cannot create sub-division under another sub-division")

        # Check if sub-division name already exists for this parent
        existing_subdivision = self.session.exec(
            select(EventDivision).where(
                EventDivision.parent_division_id == parent_division_id,
                EventDivision.name == name
            )
        ).first()

        if existing_subdivision:
            raise ValueError(f"Sub-division '{name}' already exists under '{parent_division.name}'")

        # Validate handicap ranges with existing sub-divisions
        if handicap_min is not None and handicap_max is not None:
            self._validate_handicap_range(parent_division_id, handicap_min, handicap_max)

        # Create the sub-division
        subdivision = EventDivision(
            event_id=parent_division.event_id,
            name=name,
            parent_division_id=parent_division_id,
            division_type=parent_division.division_type,
            handicap_min=handicap_min,
            handicap_max=handicap_max,
            description=description or f"Sub-division of {parent_division.name}",
            is_auto_assigned=False  # Pre-defined sub-divisions
        )

        self.session.add(subdivision)
        self.session.commit()
        self.session.refresh(subdivision)

        return subdivision

    def create_auto_subdivision(
        self,
        parent_division_id: int,
        name: str,
        handicap_min: float,
        handicap_max: float
    ) -> EventDivision:
        """
        Create an auto-assigned sub-division (for System 36 Standard, Stableford).
        These are created during winner calculation.
        """
        parent_division = self.session.get(EventDivision, parent_division_id)
        if not parent_division:
            raise ValueError(f"Parent division with id {parent_division_id} not found")

        subdivision = EventDivision(
            event_id=parent_division.event_id,
            name=name,
            parent_division_id=parent_division_id,
            division_type=parent_division.division_type,
            handicap_min=handicap_min,
            handicap_max=handicap_max,
            description=f"Auto-assigned sub-division of {parent_division.name}",
            is_auto_assigned=True
        )

        self.session.add(subdivision)
        self.session.commit()
        self.session.refresh(subdivision)

        return subdivision

    def get_divisions_tree(self, event_id: int) -> List[Dict[str, Any]]:
        """
        Get hierarchical division structure for an event.

        Returns:
            List of division dictionaries with nested sub-divisions:
            [
                {
                    "id": 1,
                    "name": "Men",
                    "parent_division_id": null,
                    "sub_divisions": [
                        {"id": 2, "name": "Men A", "parent_division_id": 1, ...},
                        {"id": 3, "name": "Men B", "parent_division_id": 1, ...}
                    ],
                    ...
                }
            ]
        """
        # Get all divisions for the event
        all_divisions = self.session.exec(
            select(EventDivision).where(
                EventDivision.event_id == event_id,
                EventDivision.is_active == True
            ).order_by(EventDivision.name)
        ).all()

        # Build tree structure
        division_map = {}
        for division in all_divisions:
            division_dict = {
                "id": division.id,
                "event_id": division.event_id,
                "name": division.name,
                "description": division.description,
                "division_type": division.division_type,
                "parent_division_id": division.parent_division_id,
                "is_auto_assigned": division.is_auto_assigned,
                "handicap_min": division.handicap_min,
                "handicap_max": division.handicap_max,
                "max_participants": division.max_participants,
                "teebox_id": division.teebox_id,
                "sub_divisions": []
            }
            division_map[division.id] = division_dict

        # Organize into tree
        root_divisions = []
        for division_dict in division_map.values():
            if division_dict["parent_division_id"] is None:
                # Root division
                root_divisions.append(division_dict)
            else:
                # Sub-division - add to parent's sub_divisions list
                parent = division_map.get(division_dict["parent_division_id"])
                if parent:
                    parent["sub_divisions"].append(division_dict)

        return root_divisions

    def _validate_handicap_range(
        self,
        parent_division_id: int,
        handicap_min: float,
        handicap_max: float
    ):
        """
        Validate that new handicap range doesn't overlap with existing sub-divisions.
        """
        if handicap_min > handicap_max:
            raise ValueError(f"handicap_min ({handicap_min}) cannot be greater than handicap_max ({handicap_max})")

        # Get existing sub-divisions for this parent
        existing_subdivisions = self.session.exec(
            select(EventDivision).where(
                EventDivision.parent_division_id == parent_division_id,
                EventDivision.is_active == True
            )
        ).all()

        for subdivision in existing_subdivisions:
            if subdivision.handicap_min is None or subdivision.handicap_max is None:
                continue

            # Check for overlap
            if not (handicap_max < subdivision.handicap_min or handicap_min > subdivision.handicap_max):
                raise ValueError(
                    f"Handicap range [{handicap_min}, {handicap_max}] overlaps with "
                    f"existing sub-division '{subdivision.name}' [{subdivision.handicap_min}, {subdivision.handicap_max}]"
                )

    def delete_subdivision(self, subdivision_id: int) -> bool:
        """
        Delete a sub-division.
        Can only delete if no participants are assigned.
        """
        subdivision = self.session.get(EventDivision, subdivision_id)
        if not subdivision:
            return False

        # Verify it's actually a sub-division
        if subdivision.parent_division_id is None:
            raise ValueError("Cannot use this method to delete a parent division")

        # Check for assigned participants
        participant_count = self.session.exec(
            select(func.count(Participant.id)).where(
                Participant.division_id == subdivision_id
            )
        ).one()

        if participant_count > 0:
            raise ValueError(
                f"Cannot delete sub-division '{subdivision.name}' - "
                f"{participant_count} participants are assigned to it"
            )

        # Hard delete (since it's a sub-division with no participants)
        self.session.delete(subdivision)
        self.session.commit()

        return True
