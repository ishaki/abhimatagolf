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
            country=participant.country,
            sex=participant.sex,
            phone_no=participant.phone_no,
            event_status=participant.event_status,
            event_description=participant.event_description,
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
            # Handle special case for empty division filtering
            if division == "__empty__":
                query = query.where(
                    (Participant.division.is_(None)) | 
                    (Participant.division == "") |
                    (Participant.division_id.is_(None))
                )
            else:
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
                    division_id=row.division_id,
                    country=row.country,
                    sex=row.sex,
                    phone_no=row.phone_no,
                    event_status=row.event_status,
                    event_description=row.event_description
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
        """
        Assign a participant to a division (including sub-divisions).

        For pre-defined sub-divisions (Net Stroke, System 36 Modified):
        - Validates handicap falls within sub-division range
        - Participant can be assigned to sub-divisions

        For auto-assigned sub-divisions (System 36 Standard, Stableford):
        - Participants should be assigned to parent division only
        - Auto-assigned sub-divisions are created during winner calculation
        """
        participant = self.session.get(Participant, participant_id)
        if not participant:
            return False

        if division_id:
            # Verify division exists and belongs to the same event
            division = self.session.get(EventDivision, division_id)
            if not division or division.event_id != participant.event_id:
                return False

            # Prevent assignment to auto-assigned sub-divisions
            if division.is_auto_assigned:
                raise ValueError(
                    f"Cannot manually assign participants to auto-assigned sub-division '{division.name}'. "
                    "Assign to parent division instead."
                )

            # For pre-defined sub-divisions, validate handicap range
            if division.parent_division_id is not None:  # This is a sub-division
                if division.handicap_min is not None and division.handicap_max is not None:
                    if participant.declared_handicap is None:
                        raise ValueError(
                            f"Cannot assign to sub-division '{division.name}' - "
                            "participant must have declared handicap"
                        )

                    if not (division.handicap_min <= participant.declared_handicap <= division.handicap_max):
                        raise ValueError(
                            f"Participant handicap {participant.declared_handicap} is outside "
                            f"sub-division '{division.name}' range [{division.handicap_min}, {division.handicap_max}]"
                        )

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

        logger.info(f"Assigned participant {participant.name} to division {division.name if division_id else 'None'}")
        return True

    def auto_assign_to_subdivisions(self, event_id: int) -> dict:
        """
        Auto-assign participants to pre-defined sub-divisions based on declared handicap.

        This is for Net Stroke and System 36 Modified events where sub-divisions are pre-defined.
        Participants are assigned to the appropriate sub-division based on their declared handicap.

        Returns:
            dict: Assignment results with counts and errors
        """
        from models.event import ScoringType, System36Variant

        # Get event and verify it uses pre-defined sub-divisions
        event = self.session.get(Event, event_id)
        if not event:
            raise ValueError(f"Event {event_id} not found")

        needs_predefined_subdivisions = (
            event.scoring_type == ScoringType.NET_STROKE or
            (event.scoring_type == ScoringType.SYSTEM_36 and
             event.system36_variant == System36Variant.MODIFIED)
        )

        if not needs_predefined_subdivisions:
            return {
                "total": 0,
                "assigned": 0,
                "skipped": 0,
                "errors": [{
                    "participant_name": "All",
                    "reason": f"Event scoring type {event.scoring_type.value} does not use pre-defined sub-divisions"
                }]
            }

        # Get all pre-defined sub-divisions for this event
        subdivisions_query = select(EventDivision).where(
            EventDivision.event_id == event_id,
            EventDivision.is_active == True,
            EventDivision.parent_division_id.is_not(None),
            EventDivision.is_auto_assigned == False
        ).order_by(EventDivision.handicap_min)

        subdivisions = list(self.session.exec(subdivisions_query).all())

        if not subdivisions:
            return {
                "total": 0,
                "assigned": 0,
                "skipped": 0,
                "errors": [{
                    "participant_name": "All",
                    "reason": "No pre-defined sub-divisions configured for this event"
                }]
            }

        # Get participants that need division assignment
        # Only those without division or in parent divisions
        parent_division_ids = list(set(s.parent_division_id for s in subdivisions if s.parent_division_id))

        participants_query = select(Participant).where(
            Participant.event_id == event_id
        )

        participants = list(self.session.exec(participants_query).all())

        # Filter eligible participants
        eligible_participants = []
        for participant in participants:
            # Skip if already in a sub-division
            if participant.division_id:
                division = self.session.get(EventDivision, participant.division_id)
                if division and division.parent_division_id is not None:
                    continue  # Already in a sub-division

            # Skip if no declared handicap
            if participant.declared_handicap is None:
                continue

            eligible_participants.append(participant)

        if not eligible_participants:
            return {
                "total": len(participants),
                "assigned": 0,
                "skipped": len(participants),
                "errors": [{
                    "participant_name": "All",
                    "reason": "No eligible participants found (all already assigned or missing handicap)"
                }]
            }

        # Assignment logic
        assigned_count = 0
        skipped_count = 0
        errors = []

        for participant in eligible_participants:
            try:
                # Find matching sub-division based on declared handicap
                matching_subdivision = None

                for subdivision in subdivisions:
                    if subdivision.handicap_min is None or subdivision.handicap_max is None:
                        continue

                    if subdivision.handicap_min <= participant.declared_handicap <= subdivision.handicap_max:
                        # Check capacity
                        if subdivision.max_participants:
                            current_count = self.session.exec(
                                select(func.count(Participant.id)).where(
                                    Participant.division_id == subdivision.id
                                )
                            ).one()

                            if current_count >= subdivision.max_participants:
                                continue  # Try next sub-division

                        matching_subdivision = subdivision
                        break

                if matching_subdivision:
                    # Assign participant to sub-division
                    participant.division_id = matching_subdivision.id
                    participant.division = matching_subdivision.name
                    self.session.add(participant)
                    assigned_count += 1

                    logger.info(f"Auto-assigned {participant.name} to {matching_subdivision.name} "
                              f"(handicap: {participant.declared_handicap})")
                else:
                    errors.append({
                        "participant_name": participant.name,
                        "reason": f"No sub-division found for handicap {participant.declared_handicap}"
                    })
                    skipped_count += 1

            except Exception as e:
                errors.append({
                    "participant_name": participant.name,
                    "reason": f"Assignment error: {str(e)}"
                })
                skipped_count += 1
                logger.error(f"Error auto-assigning {participant.name}: {str(e)}")

        # Commit all changes
        self.session.commit()

        logger.info(f"Sub-division auto-assignment completed for event {event_id}: "
                   f"{assigned_count} assigned, {skipped_count} skipped")

        return {
            "total": len(eligible_participants),
            "assigned": assigned_count,
            "skipped": skipped_count,
            "errors": errors
        }

    def assign_men_divisions_by_course_handicap(self, event_id: int) -> dict:
        """
        Assign Men divisions (A/B/C) based on course handicap for System 36 events.
        
        This method is specifically for System 36 Standard variant where Men divisions
        are assigned after teeboxes are assigned and course handicaps are calculated.
        
        Args:
            event_id: Event ID to process
            
        Returns:
            dict: Assignment results with counts and errors
        """
        from models.event import ScoringType, System36Variant
        
        # Get event and verify it's System 36
        event = self.session.get(Event, event_id)
        if not event:
            raise ValueError(f"Event {event_id} not found")
            
        if event.scoring_type != ScoringType.SYSTEM_36:
            raise ValueError(f"Event {event_id} is not a System 36 event")
            
        if event.system36_variant != System36Variant.STANDARD:
            raise ValueError(f"Event {event_id} is not using System 36 Standard variant")
        
        # Get Men divisions that use course handicap for assignment
        men_divisions_query = select(EventDivision).where(
            EventDivision.event_id == event_id,
            EventDivision.is_active == True,
            EventDivision.division_type == "men",
            EventDivision.use_course_handicap_for_assignment == True
        ).order_by(EventDivision.handicap_min)
        
        men_divisions = list(self.session.exec(men_divisions_query).all())
        
        if not men_divisions:
            return {
                "total": 0,
                "assigned": 0,
                "skipped": 0,
                "errors": [{"participant_name": "All", "reason": "No Men divisions configured for course handicap assignment"}]
            }
        
        # Get participants that need Men division assignment
        # Include participants without division or in generic "Men" division
        participants_query = select(Participant).where(
            Participant.event_id == event_id,
            Participant.division_id.is_(None) | 
            Participant.division.in_(["Men", "men", "MEN"]) |
            Participant.division_id.in_([d.id for d in men_divisions if "Men" in d.name])
        )
        
        participants = list(self.session.exec(participants_query).all())
        
        # Filter to only male participants or those not in Ladies/Senior/VIP divisions
        eligible_participants = []
        for participant in participants:
            # Skip if already in Ladies/Senior/VIP divisions
            if participant.division and any(keyword in participant.division.lower() 
                                        for keyword in ["ladies", "women", "senior", "vip"]):
                continue
                
            # Include if male or if no sex specified (assume male for Men divisions)
            if (not participant.sex or 
                participant.sex.lower() in ["male", "m"] or
                participant.sex.lower() not in ["female", "f"]):
                eligible_participants.append(participant)
        
        if not eligible_participants:
            return {
                "total": len(participants),
                "assigned": 0,
                "skipped": len(participants),
                "errors": [{"participant_name": "All", "reason": "No eligible participants found for Men division assignment"}]
            }
        
        # Assignment logic
        assigned_count = 0
        skipped_count = 0
        errors = []
        
        for participant in eligible_participants:
            try:
                # Check if participant has course handicap calculated
                if not hasattr(participant, 'course_handicap') or participant.course_handicap is None:
                    errors.append({
                        "participant_name": participant.name,
                        "reason": "Course handicap not calculated (teebox may not be assigned)"
                    })
                    skipped_count += 1
                    continue
                
                # Find matching division based on course handicap
                matching_division = None
                for division in men_divisions:
                    min_fits = division.handicap_min is None or participant.course_handicap >= division.handicap_min
                    max_fits = division.handicap_max is None or participant.course_handicap <= division.handicap_max
                    
                    if min_fits and max_fits:
                        # Check capacity
                        if division.max_participants:
                            current_count = self.session.exec(
                                select(func.count(Participant.id)).where(
                                    Participant.division_id == division.id
                                )
                            ).one()
                            
                            if current_count >= division.max_participants:
                                continue  # Try next division
                        
                        matching_division = division
                        break
                
                if matching_division:
                    # Assign participant to division
                    participant.division_id = matching_division.id
                    participant.division = matching_division.name
                    self.session.add(participant)
                    assigned_count += 1
                    
                    logger.info(f"Assigned {participant.name} to {matching_division.name} "
                              f"(course handicap: {participant.course_handicap})")
                else:
                    errors.append({
                        "participant_name": participant.name,
                        "reason": f"No Men division found for course handicap {participant.course_handicap}"
                    })
                    skipped_count += 1
                    
            except Exception as e:
                errors.append({
                    "participant_name": participant.name,
                    "reason": f"Assignment error: {str(e)}"
                })
                skipped_count += 1
                logger.error(f"Error assigning {participant.name}: {str(e)}")
        
        # Commit all changes
        self.session.commit()
        
        logger.info(f"Men division assignment completed for event {event_id}: "
                   f"{assigned_count} assigned, {skipped_count} skipped")
        
        return {
            "total": len(eligible_participants),
            "assigned": assigned_count,
            "skipped": skipped_count,
            "errors": errors
        }