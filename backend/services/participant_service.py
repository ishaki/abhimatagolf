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

    def validate_participant_division_for_system36_modified(
        self,
        participant: Participant,
        division: Optional[EventDivision] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate participant's declared handicap against division range for System 36 Modified.

        For System 36 Modified mode, declared handicap is required and should fall within
        the division's handicap range. Returns a warning (not error) if mismatch is detected,
        allowing admin to override.

        Args:
            participant: Participant to validate
            division: EventDivision (if None, will fetch from participant.division_id)

        Returns:
            Tuple of (is_valid, warning_message)
            - is_valid: True if valid or no validation needed, False if warning should be shown
            - warning_message: Description of the warning (None if valid)
        """
        from models.event import ScoringType, System36Variant

        # Get event
        event = self.session.get(Event, participant.event_id)
        if not event:
            return (True, None)  # Event not found, skip validation

        # Only validate for System 36 Modified
        if event.scoring_type != ScoringType.SYSTEM_36 or event.system36_variant != System36Variant.MODIFIED:
            return (True, None)  # Not System 36 Modified, no validation needed

        # Check if participant has declared handicap
        if participant.declared_handicap is None:
            return (False, "Declared handicap is required for System 36 Modified mode")

        # Get division if not provided
        if division is None and participant.division_id:
            division = self.session.get(EventDivision, participant.division_id)

        # If no division assigned, no validation needed
        if not division:
            return (True, None)

        # Check if division has handicap range defined
        if division.handicap_min is None or division.handicap_max is None:
            return (True, None)  # No range defined, skip validation

        # Validate handicap is within division range
        if not (division.handicap_min <= participant.declared_handicap <= division.handicap_max):
            warning = (
                f"Warning: Declared handicap {participant.declared_handicap} is outside "
                f"division '{division.name}' range [{division.handicap_min}, {division.handicap_max}]. "
                f"You can override and save anyway."
            )
            return (False, warning)

        return (True, None)  # Valid

    def create_participant(
        self,
        participant_data: ParticipantCreate
    ) -> Tuple[Participant, Optional[str]]:
        """
        Create a new participant

        Returns:
            Tuple of (participant, warning_message)
            - participant: Created participant
            - warning_message: Validation warning (None if no warnings)
        """
        # Verify event exists
        event = self.session.get(Event, participant_data.event_id)
        if not event:
            raise ValueError(f"Event with id {participant_data.event_id} not found")

        participant = Participant(**participant_data.model_dump())

        # Validate division for System 36 Modified (returns warning, doesn't block)
        division = None
        if participant.division_id:
            division = self.session.get(EventDivision, participant.division_id)

        is_valid, warning = self.validate_participant_division_for_system36_modified(participant, division)

        self.session.add(participant)
        self.session.commit()
        self.session.refresh(participant)

        logger.info(f"Created participant: {participant.name} for event {participant_data.event_id}" +
                   (f" with warning: {warning}" if warning else ""))
        return participant, warning

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

        # Normalize sex field to match enum (Male/Female)
        sex_value = None
        if participant.sex:
            sex_lower = participant.sex.lower()
            if sex_lower in ['male', 'm']:
                sex_value = 'Male'
            elif sex_lower in ['female', 'f']:
                sex_value = 'Female'
            else:
                sex_value = participant.sex.title()
        
        return ParticipantResponse(
            id=participant.id,
            event_id=participant.event_id,
            name=participant.name,
            declared_handicap=participant.declared_handicap,
            division=participant.division,
            division_id=participant.division_id,
            registered_at=participant.registered_at,
            country=participant.country,
            sex=sex_value,
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
    ) -> Tuple[Optional[Participant], Optional[str]]:
        """
        Update participant information

        Returns:
            Tuple of (participant, warning_message)
            - participant: Updated participant (None if not found)
            - warning_message: Validation warning (None if no warnings)
        """
        participant = self.session.get(Participant, participant_id)
        if not participant:
            return None, None

        # Update fields
        update_data = participant_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(participant, key, value)

        # Validate division for System 36 Modified (returns warning, doesn't block)
        division = None
        if participant.division_id:
            division = self.session.get(EventDivision, participant.division_id)

        is_valid, warning = self.validate_participant_division_for_system36_modified(participant, division)

        self.session.add(participant)
        self.session.commit()
        self.session.refresh(participant)

        logger.info(f"Updated participant {participant_id}: {participant.name}" +
                   (f" with warning: {warning}" if warning else ""))
        return participant, warning

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

    def reassign_men_divisions_by_system36_handicap(self, event_id: int) -> dict:
        """
        Reassign Men divisions (A/B/C/D) based on System 36 handicap for System 36 Standard events.

        This method is specifically for System 36 Standard variant where Men divisions
        are re-assigned after participants complete their rounds and System 36 handicaps
        are calculated from their points.

        Flow:
        1. Get all Men participants (identified by division containing "Men")
        2. Calculate System 36 handicap for each (36 - total_points)
        3. Reassign to appropriate Men division based on System 36 handicap and division ranges
        4. Skip Ladies, Seniors, and other divisions (no re-assignment)

        Args:
            event_id: Event ID to process

        Returns:
            dict: Assignment results with counts and errors
        """
        from models.event import ScoringType, System36Variant
        from models.scorecard import Scorecard
        from services.scoring_strategies import ScoringStrategyFactory

        # Get event and verify it's System 36 Standard
        event = self.session.get(Event, event_id)
        if not event:
            raise ValueError(f"Event {event_id} not found")

        if event.scoring_type != ScoringType.SYSTEM_36:
            raise ValueError(f"Event {event_id} is not a System 36 event")

        if event.system36_variant != System36Variant.STANDARD:
            raise ValueError(f"Event {event_id} is not using System 36 Standard variant")

        # Get System 36 scoring strategy
        strategy = ScoringStrategyFactory.get_strategy(ScoringType.SYSTEM_36)

        # Get Men divisions configured for this event
        # These should have handicap ranges defined
        men_divisions_query = select(EventDivision).where(
            EventDivision.event_id == event_id,
            EventDivision.is_active == True,
            EventDivision.division_type == "men"
        ).order_by(EventDivision.handicap_min)

        men_divisions = list(self.session.exec(men_divisions_query).all())

        if not men_divisions:
            return {
                "total": 0,
                "assigned": 0,
                "skipped": 0,
                "errors": [{"participant_name": "All", "reason": "No Men divisions configured for this event"}]
            }

        # Get all participants for this event
        participants_query = select(Participant).where(
            Participant.event_id == event_id
        )
        participants = list(self.session.exec(participants_query).all())

        # Filter to only Men participants (exclude Ladies, Seniors, VIP, etc.)
        eligible_participants = []
        for participant in participants:
            # Identify Men participants by division name containing "Men" or "men"
            if participant.division and "men" in participant.division.lower():
                # Exclude Ladies, Senior Men, VIP, etc.
                if not any(keyword in participant.division.lower()
                          for keyword in ["ladies", "women", "senior", "vip"]):
                    eligible_participants.append(participant)

        if not eligible_participants:
            return {
                "total": len(participants),
                "assigned": 0,
                "skipped": len(participants),
                "errors": [{"participant_name": "All", "reason": "No eligible Men participants found for re-assignment"}]
            }

        # Assignment logic
        assigned_count = 0
        skipped_count = 0
        errors = []

        for participant in eligible_participants:
            try:
                # Get all scorecards for this participant
                scorecards_query = select(Scorecard).where(
                    Scorecard.participant_id == participant.id,
                    Scorecard.strokes > 0
                )
                scorecards = list(self.session.exec(scorecards_query).all())

                if not scorecards:
                    errors.append({
                        "participant_name": participant.name,
                        "reason": "No scorecards found - participant hasn't completed any holes"
                    })
                    skipped_count += 1
                    continue

                # Calculate total points and holes completed
                total_points = sum(scorecard.points or 0 for scorecard in scorecards)
                holes_completed = len(scorecards)

                # Calculate System 36 handicap (only for complete 18-hole rounds)
                system36_handicap = strategy.calculate_system36_handicap(total_points, holes_completed)

                if holes_completed != 18:
                    errors.append({
                        "participant_name": participant.name,
                        "reason": f"Incomplete round ({holes_completed}/18 holes) - System 36 handicap not calculated"
                    })
                    skipped_count += 1
                    continue

                # Find matching Men division based on System 36 handicap
                matching_division = None
                for division in men_divisions:
                    min_fits = division.handicap_min is None or system36_handicap >= division.handicap_min
                    max_fits = division.handicap_max is None or system36_handicap <= division.handicap_max

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
                    # Reassign participant to new division
                    old_division = participant.division
                    participant.division_id = matching_division.id
                    participant.division = matching_division.name
                    self.session.add(participant)
                    assigned_count += 1

                    logger.info(f"Reassigned {participant.name} from {old_division} to {matching_division.name} "
                              f"(System 36 handicap: {system36_handicap}, Points: {total_points})")
                else:
                    errors.append({
                        "participant_name": participant.name,
                        "reason": f"No Men division found for System 36 handicap {system36_handicap}"
                    })
                    skipped_count += 1

            except Exception as e:
                errors.append({
                    "participant_name": participant.name,
                    "reason": f"Reassignment error: {str(e)}"
                })
                skipped_count += 1
                logger.error(f"Error reassigning {participant.name}: {str(e)}")

        # Commit all changes
        self.session.commit()

        logger.info(f"Men division reassignment (System 36 Standard) completed for event {event_id}: "
                   f"{assigned_count} reassigned, {skipped_count} skipped")

        return {
            "total": len(eligible_participants),
            "reassigned": assigned_count,
            "skipped": skipped_count,
            "errors": errors
        }