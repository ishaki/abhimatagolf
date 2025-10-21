from sqlmodel import Session, select, func
from typing import Optional, List, Tuple
from models.participant import Participant
from models.event import Event
from models.event_division import EventDivision
from schemas.participant import (
    ParticipantCreate, ParticipantUpdate, ParticipantResponse,
    ParticipantBulkCreate, ParticipantStats, ParticipantImportRow
)
from core.app_logging import logger


class ParticipantService:
    def __init__(self, session: Session):
        self.session = session

    def create_participant(
        self,
        participant_data: ParticipantCreate
    ) -> Participant:
        """Create a new participant"""
        # Verify event exists
        event = self.session.get(Event, participant_data.event_id)
        if not event:
            raise ValueError(f"Event with id {participant_data.event_id} not found")

        participant = Participant(**participant_data.model_dump())
        self.session.add(participant)
        self.session.commit()
        self.session.refresh(participant)

        logger.info(f"Created participant: {participant.name} for event {participant_data.event_id}")
        return participant

    def create_participants_bulk(
        self,
        participants_data: ParticipantBulkCreate
    ) -> List[Participant]:
        """Create multiple participants at once"""
        # Verify event exists
        event = self.session.get(Event, participants_data.event_id)
        if not event:
            raise ValueError(f"Event with id {participants_data.event_id} not found")

        created_participants = []
        for participant_base in participants_data.participants:
            participant_dict = participant_base.model_dump()
            participant_dict['event_id'] = participants_data.event_id
            participant = Participant(**participant_dict)
            self.session.add(participant)
            created_participants.append(participant)

        self.session.commit()

        # Refresh all participants
        for participant in created_participants:
            self.session.refresh(participant)

        logger.info(f"Created {len(created_participants)} participants for event {participants_data.event_id}")
        return created_participants

    def get_participant(self, participant_id: int) -> Optional[Participant]:
        """Get a single participant by ID"""
        return self.session.get(Participant, participant_id)

    def get_participant_with_details(self, participant_id: int) -> Optional[ParticipantResponse]:
        """Get participant with additional details"""
        participant = self.session.get(Participant, participant_id)
        if not participant:
            return None

        # Get event name
        event = self.session.get(Event, participant.event_id)
        event_name = event.name if event else None

        # Get scorecard count
        from models.scorecard import Scorecard
        scorecard_count = self.session.exec(
            select(func.count(Scorecard.id))
            .where(Scorecard.participant_id == participant_id)
        ).one()

        # Get scoring totals
        scorecard_stats = self.session.exec(
            select(
                func.coalesce(func.sum(Scorecard.strokes), 0),
                func.coalesce(func.sum(Scorecard.net_score), 0),
                func.coalesce(func.sum(Scorecard.points), 0)
            )
            .where(Scorecard.participant_id == participant_id)
        ).one()

        return ParticipantResponse(
            id=participant.id,
            event_id=participant.event_id,
            name=participant.name,
            declared_handicap=participant.declared_handicap,
            division=participant.division,
            division_id=participant.division_id,
            registered_at=participant.registered_at,
            event_name=event_name,
            scorecard_count=scorecard_count,
            total_gross_score=int(scorecard_stats[0]),
            total_net_score=float(scorecard_stats[1]),
            total_points=int(scorecard_stats[2])
        )

    def get_participants(
        self,
        page: int = 1,
        per_page: int = 10,
        search: Optional[str] = None,
        event_id: Optional[int] = None,
        division: Optional[str] = None,
        division_id: Optional[int] = None
    ) -> Tuple[List[Participant], int]:
        """Get participants with filtering and pagination"""
        # Build query
        query = select(Participant)

        # Apply filters
        if search:
            query = query.where(Participant.name.ilike(f"%{search}%"))
        if event_id:
            query = query.where(Participant.event_id == event_id)
        if division:
            query = query.where(Participant.division == division)
        if division_id:
            query = query.where(Participant.division_id == division_id)

        # Get total count
        total_query = select(func.count()).select_from(query.subquery())
        total = self.session.exec(total_query).one()

        # Apply pagination and ordering
        query = query.order_by(Participant.registered_at.desc())
        query = query.offset((page - 1) * per_page).limit(per_page)

        participants = self.session.exec(query).all()

        return participants, total

    def update_participant(
        self,
        participant_id: int,
        participant_data: ParticipantUpdate
    ) -> Optional[Participant]:
        """Update participant information"""
        participant = self.session.get(Participant, participant_id)
        if not participant:
            return None

        # Update fields
        update_data = participant_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(participant, key, value)

        self.session.add(participant)
        self.session.commit()
        self.session.refresh(participant)

        logger.info(f"Updated participant {participant_id}: {participant.name}")
        return participant

    def delete_participant(self, participant_id: int) -> bool:
        """Delete a participant"""
        participant = self.session.get(Participant, participant_id)
        if not participant:
            return False

        self.session.delete(participant)
        self.session.commit()

        logger.info(f"Deleted participant {participant_id}: {participant.name}")
        return True

    def get_event_participants(self, event_id: int) -> List[Participant]:
        """Get all participants for a specific event"""
        query = select(Participant).where(Participant.event_id == event_id)
        query = query.order_by(Participant.name)
        return self.session.exec(query).all()

    def get_participant_stats(self, event_id: Optional[int] = None) -> ParticipantStats:
        """Get participant statistics"""
        query = select(Participant)
        if event_id:
            query = query.where(Participant.event_id == event_id)

        participants = self.session.exec(query).all()

        # Calculate stats
        total = len(participants)

        # Group by division
        by_division = {}
        for participant in participants:
            division = participant.division or 'Unassigned'
            by_division[division] = by_division.get(division, 0) + 1

        # Calculate average handicap
        total_handicap = sum(p.declared_handicap for p in participants)
        average_handicap = total_handicap / total if total > 0 else 0

        return ParticipantStats(
            total_participants=total,
            by_division=by_division,
            average_handicap=round(average_handicap, 2)
        )

    def import_participants_from_list(
        self,
        event_id: int,
        participant_rows: List[ParticipantImportRow]
    ) -> Tuple[List[Participant], List[dict]]:
        """Import participants from a list of validated rows"""
        # Verify event exists
        event = self.session.get(Event, event_id)
        if not event:
            raise ValueError(f"Event with id {event_id} not found")

        created_participants = []
        errors = []

        for idx, row in enumerate(participant_rows):
            try:
                # Validate division_id if provided
                if row.division_id is not None:
                    # Check if the division exists
                    division = self.session.get(EventDivision, row.division_id)
                    if not division or division.event_id != event_id:
                        errors.append({
                            'row': idx + 1,
                            'name': row.name,
                            'error': f'Invalid division_id {row.division_id} for event {event_id}'
                        })
                        continue
                
                participant = Participant(
                    event_id=event_id,
                    name=row.name,
                    declared_handicap=row.declared_handicap,
                    division=row.division,
                    division_id=row.division_id
                )
                self.session.add(participant)
                created_participants.append(participant)
            except Exception as e:
                errors.append({
                    'row': idx + 1,
                    'name': row.name,
                    'error': str(e)
                })

        if created_participants:
            self.session.commit()
            for participant in created_participants:
                self.session.refresh(participant)

        logger.info(f"Imported {len(created_participants)} participants with {len(errors)} errors")
        return created_participants, errors

    def search_participants(
        self,
        search_term: str,
        event_id: Optional[int] = None,
        limit: int = 20
    ) -> List[Participant]:
        """Search participants by name"""
        query = select(Participant).where(
            Participant.name.ilike(f"%{search_term}%")
        )

        if event_id:
            query = query.where(Participant.event_id == event_id)

        query = query.limit(limit)
        return self.session.exec(query).all()

    def get_divisions_for_event(self, event_id: int) -> List[str]:
        """Get list of unique divisions for an event (legacy method for backward compatibility)"""
        # First try to get from EventDivision table
        divisions_query = select(EventDivision.name).where(
            EventDivision.event_id == event_id,
            EventDivision.is_active == True
        ).order_by(EventDivision.name)
        
        event_divisions = self.session.exec(divisions_query).all()
        
        if event_divisions:
            return list(event_divisions)
        
        # Fallback to old method (participant.division field)
        query = select(Participant.division).where(
            Participant.event_id == event_id,
            Participant.division.is_not(None)
        ).distinct()

        divisions = self.session.exec(query).all()
        return [d for d in divisions if d]

    def get_event_divisions(self, event_id: int) -> List[EventDivision]:
        """Get EventDivision objects for an event"""
        query = select(EventDivision).where(
            EventDivision.event_id == event_id,
            EventDivision.is_active == True
        ).order_by(EventDivision.name)
        
        return self.session.exec(query).all()

    def assign_participant_to_division(self, participant_id: int, division_id: Optional[int]) -> bool:
        """Assign a participant to a division"""
        participant = self.session.get(Participant, participant_id)
        if not participant:
            return False
        
        if division_id:
            # Verify division exists and belongs to the same event
            division = self.session.get(EventDivision, division_id)
            if not division or division.event_id != participant.event_id:
                return False
            
            # Check division capacity
            if division.max_participants:
                current_count = self.session.exec(
                    select(func.count(Participant.id)).where(
                        Participant.division_id == division_id
                    )
                ).one()
                
                if current_count >= division.max_participants:
                    raise ValueError(f"Division '{division.name}' is at maximum capacity")
            
            participant.division_id = division_id
            participant.division = division.name  # Keep legacy field in sync
        else:
            participant.division_id = None
            participant.division = None
        
        self.session.add(participant)
        self.session.commit()
        return True
