"""
Winner Service - Calculate tournament winners with tie-breaking

This service calculates winners for golf tournaments, handling:
- Overall winners
- Division winners
- Tie-breaking using standard golf rules
- Strategy Pattern for scoring-type-specific winner calculation

Architecture:
- Uses WinnerStrategyFactory to get appropriate strategy based on scoring type
- Each strategy defines: primary metric, sort order, tie-breaking, eligibility
- Supports Stroke, Net Stroke, System 36, and future Stableford
"""

from typing import List, Dict, Any, Optional, Tuple
from sqlmodel import Session, select
from models.winner_result import WinnerResult
from models.event import Event, ScoringType, System36Variant
from models.participant import Participant
from models.scorecard import Scorecard
from models.event_division import EventDivision
from models.winner_configuration import WinnerConfiguration
from services.winner_strategies import WinnerStrategyFactory
from datetime import datetime
from core.app_logging import logger


class WinnerService:
    """Service for calculating and managing tournament winners"""

    @staticmethod
    def calculate_winners(session: Session, event_id: int, user_id: Optional[int] = None) -> List[WinnerResult]:
        """
        Calculate winners for an event with proper tie-breaking.

        Uses event's winner configuration to determine calculation rules.
        Only creates WinnerResult records for actual winners (based on configuration).

        Args:
            session: Database session
            event_id: Event ID to calculate winners for
            user_id: Optional user ID for creating default config if needed

        Returns:
            List of WinnerResult objects (only winners, not all participants)

        Raises:
            ValueError: If event not found or has no scorecards
        """
        # Get event
        event = session.get(Event, event_id)
        if not event:
            raise ValueError(f"Event {event_id} not found")

        # Get winner configuration (create default if not exists)
        from services.winner_configuration_service import WinnerConfigurationService
        config = WinnerConfigurationService.get_config_by_event(session, event_id)
        if not config and user_id:
            config = WinnerConfigurationService.create_default_config(session, event_id, user_id)
            logger.info(f"Created default winner configuration for event {event_id}")

        # Get all participants for the event
        participants_query = select(Participant).where(Participant.event_id == event_id)
        participants = list(session.exec(participants_query).all())

        if not participants:
            raise ValueError(f"No participants found for event {event_id}")

        # Clear existing winner results
        WinnerService._clear_existing_winners(session, event_id)

        # Build participant scorecards with totals
        participant_scorecards = WinnerService._build_participant_scorecards(session, event, participants)

        # Filter participants based on configuration and scoring type strategy
        if config:
            participant_scorecards = WinnerService._filter_by_eligibility(
                participant_scorecards,
                event,
                config
            )

        # Step 1: Calculate special awards FIRST (Best Gross, Best Net) with cascading exclusion
        special_award_winners, excluded_participant_ids = WinnerService._calculate_special_awards(
            session, event, participant_scorecards, config
        )

        # Step 2: Filter out special award winners from division calculation pool
        participant_scorecards_for_divisions = [
            p_data for p_data in participant_scorecards
            if p_data['participant'].id not in excluded_participant_ids
        ]

        logger.info(
            f"Special awards: {len(special_award_winners)} winner(s), "
            f"{len(excluded_participant_ids)} participant(s) excluded from division winners"
        )

        # Step 3: Calculate division winners (from remaining participants only)
        division_winners = WinnerService._calculate_division_winners(
            session, event, participant_scorecards_for_divisions, config
        )

        # Step 4: Combine all winners (special awards first, then division winners)
        all_winners = special_award_winners + division_winners

        # Step 5: Save all winner results
        for winner in all_winners:
            session.add(winner)

        session.commit()
        logger.info(
            f"Calculated {len(all_winners)} total winner results for event {event_id} "
            f"({len(special_award_winners)} special awards, {len(division_winners)} division winners)"
        )

        return all_winners

    @staticmethod
    def _build_participant_scorecards(session: Session, event: Event, participants: List[Participant]) -> List[Dict]:
        """
        Build participant scorecards with calculated totals for tie-breaking.
        
        Returns:
            List of dictionaries with participant data and calculated scores
        """
        from models.course import Hole
        
        participant_scorecards = []
        
        # Get all holes for the course
        holes_query = select(Hole).where(Hole.course_id == event.course_id).order_by(Hole.number)
        holes = list(session.exec(holes_query).all())
        
        for participant in participants:
            # Get all scorecards for this participant
            scorecards_query = select(Scorecard).where(Scorecard.participant_id == participant.id)
            scorecards = list(session.exec(scorecards_query).all())
            
            # Create mapping of hole_id to scorecard
            scorecard_map = {sc.hole_id: sc for sc in scorecards}
            
            # Calculate totals
            gross_score = 0
            front_nine_total = 0
            back_nine_total = 0
            last_6_total = 0
            last_3_total = 0
            last_hole_score = 999
            holes_completed = 0
            
            for i, hole in enumerate(holes):
                scorecard = scorecard_map.get(hole.id)
                if scorecard and scorecard.strokes > 0:
                    strokes = scorecard.strokes
                    gross_score += strokes
                    holes_completed += 1
                    
                    # Front nine (holes 1-9)
                    if i < 9:
                        front_nine_total += strokes
                    # Back nine (holes 10-18)
                    else:
                        back_nine_total += strokes
                    
                    # Last 6 holes (holes 13-18)
                    if i >= 12:
                        last_6_total += strokes
                    
                    # Last 3 holes (holes 16-18)
                    if i >= 15:
                        last_3_total += strokes
                    
                    # Last hole
                    if i == len(holes) - 1:
                        last_hole_score = strokes
            
            # Calculate net score using course handicap (teebox-based)
            net_score = gross_score - participant.course_handicap if gross_score > 0 else None

            # Calculate System 36 points (if applicable)
            system36_points = 0
            back_nine_points = 0
            calculated_handicap = None

            if event.scoring_type == ScoringType.SYSTEM_36:
                # Calculate System 36 points (either from scorecard or on-the-fly)
                from services.scoring_strategies.system36 import System36ScoringStrategy
                system36_strategy = System36ScoringStrategy()

                # Create hole mapping for looking up hole par
                hole_map = {h.id: h for h in holes}

                for scorecard in scorecards:
                    hole = hole_map.get(scorecard.hole_id)
                    if not hole or not scorecard.strokes or scorecard.strokes == 0:
                        continue

                    # Calculate points: use scorecard.points if available and > 0, otherwise calculate on-the-fly
                    points = scorecard.points if (scorecard.points is not None and scorecard.points > 0) else \
                             system36_strategy.calculate_system36_points(scorecard.strokes, hole.par)

                    system36_points += points

                    # Track back 9 points (holes 10-18)
                    if hole.number >= 10:  # Back 9 (holes 10-18)
                        back_nine_points += points

                # Calculate System 36 handicap (only for full 18 holes)
                if holes_completed >= 18:
                    calculated_handicap = 36 - system36_points
                    # Recalculate net score using System 36 handicap
                    net_score = gross_score - calculated_handicap if gross_score > 0 else None

            # System 36 Modified: Validate calculated handicap against division ranges (Men's divisions only)
            is_disqualified = False
            disqualification_reason = None
            original_division_id = None
            division_reassigned = False

            if (event.scoring_type == ScoringType.SYSTEM_36 and
                event.system36_variant == System36Variant.MODIFIED and
                holes_completed >= 18 and
                calculated_handicap is not None and
                participant.event_division is not None):

                from models.event_division import DivisionType

                # Only validate for Men's divisions with defined handicap ranges
                if participant.event_division.division_type == DivisionType.MEN:
                    current_division = participant.event_division
                    current_min = current_division.handicap_min
                    current_max = current_division.handicap_max

                    # Skip validation if division doesn't have defined handicap ranges
                    if current_min is None or current_max is None:
                        logger.debug(
                            f"Skipping validation for {participant.name} - "
                            f"division '{current_division.name}' has no handicap range defined"
                        )
                    # Scenario A: Calculated handicap < Division Min (better player)
                    elif calculated_handicap < current_min:
                        logger.info(
                            f"System 36 Modified: Participant {participant.name} calculated handicap "
                            f"{calculated_handicap} is below division '{current_division.name}' minimum {current_min}"
                        )

                        # Find appropriate Men's division
                        new_division = WinnerService._find_appropriate_mens_division(
                            session, event.id, calculated_handicap
                        )

                        if new_division and new_division.id != current_division.id:
                            # Reassign to new division
                            logger.warning(
                                f"REASSIGNMENT: {participant.name} moved from '{current_division.name}' "
                                f"to '{new_division.name}' (calculated hcp: {calculated_handicap})"
                            )
                            original_division_id = current_division.id
                            division_reassigned = True
                            # Update participant reference (for winner calculation)
                            participant.division_id = new_division.id
                            participant.division = new_division.name
                            participant.event_division = new_division
                        else:
                            # No appropriate division found - disqualify
                            logger.warning(
                                f"DISQUALIFICATION: {participant.name} has no appropriate Men's division "
                                f"for calculated handicap {calculated_handicap}"
                            )
                            is_disqualified = True
                            disqualification_reason = (
                                f"Calculated System 36 handicap ({calculated_handicap:.1f}) is below "
                                f"division minimum and no appropriate division found"
                            )

                    # Scenario B: Calculated handicap > Division Max (worse player)
                    elif calculated_handicap > current_max:
                        logger.warning(
                            f"DISQUALIFICATION: {participant.name} calculated handicap {calculated_handicap} "
                            f"exceeds division '{current_division.name}' maximum {current_max}"
                        )
                        is_disqualified = True
                        disqualification_reason = (
                            f"Calculated System 36 handicap ({calculated_handicap:.1f}) exceeds "
                            f"division maximum ({current_max})"
                        )

            participant_data = {
                'participant': participant,
                'gross_score': gross_score if holes_completed > 0 else None,
                'net_score': net_score,
                'front_nine_total': front_nine_total,
                'back_nine_total': back_nine_total,
                'last_6_total': last_6_total,
                'last_3_total': last_3_total,
                'last_hole_score': last_hole_score,
                'holes_completed': holes_completed,
                'system36_points': system36_points,  # Total System 36 points
                'back_nine_points': back_nine_points,  # Back 9 points for tie-breaking
                'calculated_handicap': calculated_handicap,  # System 36 handicap
                # System 36 Modified validation fields
                'is_disqualified': is_disqualified,
                'disqualification_reason': disqualification_reason,
                'original_division_id': original_division_id,
                'division_reassigned': division_reassigned,
            }

            participant_scorecards.append(participant_data)
        
        return participant_scorecards

    @staticmethod
    def _filter_by_eligibility(
        participant_scorecards: List[Dict],
        event: Event,
        config: WinnerConfiguration
    ) -> List[Dict]:
        """
        Filter participants based on eligibility rules using strategy pattern

        Uses the scoring-type-specific strategy to determine eligibility.
        Different scoring types have different requirements:
        - Stroke/Net: Configurable minimum holes
        - System 36: Must have 18 holes (hard requirement)

        Args:
            participant_scorecards: List of participant data
            event: Event with scoring type
            config: Winner configuration

        Returns:
            Filtered list of eligible participants
        """
        # Get strategy for this scoring type
        strategy = WinnerStrategyFactory.get_strategy(event.scoring_type)

        filtered = []
        for p_data in participant_scorecards:
            # Use strategy to check eligibility
            if strategy.is_eligible(p_data, config):
                filtered.append(p_data)
            else:
                logger.debug(
                    f"Excluding participant {p_data['participant'].name} - "
                    f"not eligible per {event.scoring_type} rules "
                    f"({p_data.get('holes_completed', 0)} holes completed)"
                )

        logger.info(f"Filtered {len(participant_scorecards)} participants to {len(filtered)} eligible")
        return filtered

    @staticmethod
    def _clear_existing_winners(session: Session, event_id: int):
        """Clear existing winner results for an event"""
        existing_winners = session.exec(
            select(WinnerResult).where(WinnerResult.event_id == event_id)
        ).all()
        for winner in existing_winners:
            session.delete(winner)

    @staticmethod
    def _calculate_special_awards(
        session: Session,
        event: Event,
        participant_scorecards: List[Dict],
        config: Optional[WinnerConfiguration] = None
    ) -> Tuple[List[WinnerResult], set]:
        """
        Calculate special award winners (Best Gross, Best Net) with cascading exclusion.

        Business Rule: One person can win ONLY ONE award/position.
        Cascading exclusion order:
        1. Best Gross winner → excluded from Best Net and Division Winners
        2. Best Net winner → excluded from Division Winners

        Args:
            session: Database session
            event: Event
            participant_scorecards: List of participant data with scores
            config: Winner configuration

        Returns:
            Tuple of:
            - List[WinnerResult]: Special award winners
            - set: Participant IDs that won special awards (for exclusion from division winners)
        """
        special_award_winners = []
        excluded_participant_ids = set()

        if not config:
            return special_award_winners, excluded_participant_ids

        # Get strategy for this scoring type
        strategy = WinnerStrategyFactory.get_strategy(event.scoring_type)

        # Step 1: Calculate Best Gross (if enabled)
        if config.include_best_gross:
            # Find participant with lowest gross score
            valid_participants = [
                p_data for p_data in participant_scorecards
                if p_data.get('gross_score') is not None and p_data['gross_score'] > 0
            ]

            if valid_participants:
                # Sort by gross score (ascending - lower is better)
                sorted_by_gross = sorted(
                    valid_participants,
                    key=lambda p: (
                        p['gross_score'],
                        p.get('back_nine_total', 999),
                        p.get('last_6_total', 999),
                        p.get('last_3_total', 999),
                        p.get('last_hole_score', 999),
                        p['participant'].declared_handicap
                    )
                )

                best_gross_data = sorted_by_gross[0]
                participant = best_gross_data['participant']

                # Get teebox information
                teebox_name = participant.teebox.name if participant.teebox else None
                teebox_course_rating = participant.teebox.course_rating if participant.teebox else None
                teebox_slope_rating = participant.teebox.slope_rating if participant.teebox else None

                # Get System 36 handicap if applicable
                system36_handicap = None
                if event.scoring_type == ScoringType.SYSTEM_36:
                    system36_handicap = best_gross_data.get('calculated_handicap')

                # Create winner result
                best_gross_winner = WinnerResult(
                    event_id=event.id,
                    participant_id=participant.id,
                    participant_name=participant.name,
                    division=participant.division,
                    division_id=participant.division_id,
                    overall_rank=None,  # Not applicable for special awards
                    division_rank=None,  # Not applicable for special awards
                    gross_score=best_gross_data['gross_score'],
                    net_score=best_gross_data.get('net_score'),
                    declared_handicap=participant.declared_handicap,
                    course_handicap=participant.course_handicap,
                    system36_handicap=system36_handicap,
                    teebox_name=teebox_name,
                    teebox_course_rating=teebox_course_rating,
                    teebox_slope_rating=teebox_slope_rating,
                    award_category="Best Gross",  # Special award category
                    is_tied=False,
                    calculated_at=datetime.utcnow()
                )

                special_award_winners.append(best_gross_winner)
                excluded_participant_ids.add(participant.id)

                logger.info(
                    f"Best Gross Award: {participant.name} (Gross: {best_gross_data['gross_score']}) "
                    f"- excluded from subsequent winner selections"
                )

        # Step 2: Calculate Best Net (if enabled and scoring type supports net)
        if config.include_best_net and event.scoring_type in [ScoringType.NET_STROKE, ScoringType.SYSTEM_36]:
            # Filter out Best Gross winner (cascading exclusion)
            remaining_participants = [
                p_data for p_data in participant_scorecards
                if p_data['participant'].id not in excluded_participant_ids
                and p_data.get('net_score') is not None
            ]

            if remaining_participants:
                # Sort by net score (ascending - lower is better)
                sorted_by_net = sorted(
                    remaining_participants,
                    key=lambda p: (
                        p['net_score'],
                        p.get('back_nine_total', 999),
                        p.get('last_6_total', 999),
                        p.get('last_3_total', 999),
                        p.get('last_hole_score', 999),
                        p['participant'].declared_handicap
                    )
                )

                best_net_data = sorted_by_net[0]
                participant = best_net_data['participant']

                # Get teebox information
                teebox_name = participant.teebox.name if participant.teebox else None
                teebox_course_rating = participant.teebox.course_rating if participant.teebox else None
                teebox_slope_rating = participant.teebox.slope_rating if participant.teebox else None

                # Get System 36 handicap if applicable
                system36_handicap = None
                if event.scoring_type == ScoringType.SYSTEM_36:
                    system36_handicap = best_net_data.get('calculated_handicap')

                # Create winner result
                best_net_winner = WinnerResult(
                    event_id=event.id,
                    participant_id=participant.id,
                    participant_name=participant.name,
                    division=participant.division,
                    division_id=participant.division_id,
                    overall_rank=None,  # Not applicable for special awards
                    division_rank=None,  # Not applicable for special awards
                    gross_score=best_net_data['gross_score'],
                    net_score=best_net_data['net_score'],
                    declared_handicap=participant.declared_handicap,
                    course_handicap=participant.course_handicap,
                    system36_handicap=system36_handicap,
                    teebox_name=teebox_name,
                    teebox_course_rating=teebox_course_rating,
                    teebox_slope_rating=teebox_slope_rating,
                    award_category="Best Net",  # Special award category
                    is_tied=False,
                    calculated_at=datetime.utcnow()
                )

                special_award_winners.append(best_net_winner)
                excluded_participant_ids.add(participant.id)

                logger.info(
                    f"Best Net Award: {participant.name} (Net: {best_net_data['net_score']}) "
                    f"- excluded from division winner selections"
                )

        return special_award_winners, excluded_participant_ids

    @staticmethod
    def _find_appropriate_mens_division(
        session: Session,
        event_id: int,
        calculated_handicap: float
    ) -> Optional[EventDivision]:
        """
        Find appropriate Men's division for a calculated System 36 handicap.

        Returns the Men's division where:
        - handicap_min <= calculated_handicap <= handicap_max
        - division_type == 'men'

        Args:
            session: Database session
            event_id: Event ID
            calculated_handicap: Calculated System 36 handicap (36 - total points)

        Returns:
            EventDivision if found, None otherwise
        """
        from models.event_division import DivisionType

        query = (
            select(EventDivision)
            .where(EventDivision.event_id == event_id)
            .where(EventDivision.division_type == DivisionType.MEN)
            .where(EventDivision.handicap_min <= calculated_handicap)
            .where(EventDivision.handicap_max >= calculated_handicap)
            .where(EventDivision.is_active == True)
            .order_by(EventDivision.handicap_min)  # Prefer lower handicap divisions
        )

        division = session.exec(query).first()

        if division:
            logger.info(
                f"Found appropriate Men's division '{division.name}' "
                f"for calculated handicap {calculated_handicap} "
                f"(range: {division.handicap_min}-{division.handicap_max})"
            )
        else:
            logger.warning(
                f"No appropriate Men's division found for calculated handicap {calculated_handicap} "
                f"in event {event_id}"
            )

        return division

    @staticmethod
    def _calculate_overall_winners(
        session: Session,
        event: Event,
        participant_scorecards: List[Dict],
        config: Optional[WinnerConfiguration] = None
    ) -> List[WinnerResult]:
        """Calculate overall event winners"""
        winners = []

        # Determine which score to use based on scoring type
        use_net = event.scoring_type in [ScoringType.NET_STROKE, ScoringType.SYSTEM_36]

        # Sort participant scorecards by score with tie-breaking
        sorted_participants = WinnerService._sort_scorecards_with_tiebreak(
            participant_scorecards, use_net, config
        )

        # Assign ranks
        current_rank = 1
        previous_score = None
        tied_participants = []

        for idx, participant_data in enumerate(sorted_participants):
            participant = participant_data['participant']
            
            # Get the score for ranking
            score = participant_data['net_score'] if use_net else participant_data['gross_score']
            if score is None:
                continue

            # Check for ties
            if previous_score is not None and score != previous_score:
                # Different score - finalize tied group if any
                if len(tied_participants) > 1:
                    WinnerService._mark_ties(tied_participants)
                tied_participants = []
                current_rank = idx + 1

            # Get teebox information for transparency
            teebox_name = None
            teebox_course_rating = None
            teebox_slope_rating = None
            if participant.teebox:
                teebox_name = participant.teebox.name
                teebox_course_rating = participant.teebox.course_rating
                teebox_slope_rating = participant.teebox.slope_rating

            # Create winner result
            winner = WinnerResult(
                event_id=event.id,
                participant_id=participant.id,
                participant_name=participant.name,
                division=participant.division,
                division_id=participant.division_id,
                overall_rank=current_rank,
                gross_score=participant_data['gross_score'] or 0,
                net_score=participant_data['net_score'],
                declared_handicap=participant.declared_handicap,
                course_handicap=participant.course_handicap,
                teebox_name=teebox_name,
                teebox_course_rating=teebox_course_rating,
                teebox_slope_rating=teebox_slope_rating,
                is_tied=False,  # Will be updated if tied
                calculated_at=datetime.utcnow()
            )

            winners.append(winner)
            tied_participants.append((winner, score))
            previous_score = score

        # Handle final group of ties
        if len(tied_participants) > 1:
            WinnerService._mark_ties(tied_participants)

        return winners

    @staticmethod
    def _calculate_division_winners(
        session: Session,
        event: Event,
        participant_scorecards: List[Dict],
        config: Optional[WinnerConfiguration] = None
    ) -> List[WinnerResult]:
        """
        Calculate division-specific winners.

        Creates WinnerResult records ONLY for winners (top N per division based on config).
        Each winner gets a division_rank (1, 2, 3...) within their division.

        Args:
            session: Database session
            event: Event
            participant_scorecards: List of participant data with scores
            config: Winner configuration (determines winners_per_division)

        Returns:
            List of WinnerResult objects for division winners only
        """
        # Get divisions for the event
        divisions_query = select(EventDivision).where(EventDivision.event_id == event.id)
        divisions = list(session.exec(divisions_query).all())

        if not divisions:
            logger.warning(f"No divisions found for event {event.id}")
            return []

        # Determine number of winners per division
        winners_per_division = config.winners_per_division if config else 3

        all_division_winners = []

        # Get strategy for this scoring type
        strategy = WinnerStrategyFactory.get_strategy(event.scoring_type)

        for division in divisions:
            # Filter participant scorecards by division (exclude disqualified)
            division_participants = [
                p_data for p_data in participant_scorecards
                if p_data['participant'].division_id == division.id
                and not p_data.get('is_disqualified', False)  # Exclude disqualified participants
            ]

            if not division_participants:
                logger.info(f"No participants in division {division.name} for event {event.id}")
                continue

            # Sort division participants using strategy pattern
            sorted_participants = WinnerService._sort_scorecards_with_strategy(
                division_participants, event, config
            )

            # Track ties and ranks
            current_rank = 1
            previous_data = None
            tied_participants = []
            winners_created = 0

            # Create WinnerResult only for top N winners
            for idx, participant_data in enumerate(sorted_participants):
                participant = participant_data['participant']

                # Get the primary ranking metric from strategy
                primary_metric = strategy.get_primary_metric(participant_data)
                if primary_metric == 999 or (strategy.get_sort_order() == 'desc' and primary_metric == 0):
                    # Invalid score - skip
                    continue

                # Check if truly tied (same score AND same tie-break values)
                is_truly_tied = False
                if previous_data is not None:
                    is_truly_tied = WinnerService._check_if_tied(
                        previous_data, participant_data, event, config
                    )

                # Stop if we've created enough winners (unless there's a tie at the cutoff)
                if winners_created >= winners_per_division and not is_truly_tied:
                    break

                # Update rank if not tied
                if previous_data is not None and not is_truly_tied:
                    # Different position - finalize tied group if any
                    if len(tied_participants) > 1:
                        WinnerService._mark_ties(tied_participants)
                    tied_participants = []
                    current_rank = winners_created + 1

                # Get teebox information for transparency
                teebox_name = None
                teebox_course_rating = None
                teebox_slope_rating = None
                if participant.teebox:
                    teebox_name = participant.teebox.name
                    teebox_course_rating = participant.teebox.course_rating
                    teebox_slope_rating = participant.teebox.slope_rating

                # Get System 36 handicap if applicable
                system36_handicap = None
                if event.scoring_type == ScoringType.SYSTEM_36:
                    system36_handicap = participant_data.get('calculated_handicap')

                # Get division reassignment tracking
                original_division_id = participant_data.get('original_division_id')
                division_reassigned = participant_data.get('division_reassigned', False)

                # Create winner result
                winner = WinnerResult(
                    event_id=event.id,
                    participant_id=participant.id,
                    participant_name=participant.name,
                    division=participant.division,
                    division_id=participant.division_id,
                    overall_rank=None,  # Not used for division-only display
                    division_rank=current_rank,  # Rank within division (1, 2, 3...)
                    gross_score=participant_data['gross_score'] or 0,
                    net_score=participant_data['net_score'],
                    declared_handicap=participant.declared_handicap,
                    course_handicap=participant.course_handicap,
                    system36_handicap=system36_handicap,  # System 36 calculated handicap (36 - points)
                    teebox_name=teebox_name,
                    teebox_course_rating=teebox_course_rating,
                    teebox_slope_rating=teebox_slope_rating,
                    original_division_id=original_division_id,  # Track division change
                    division_reassigned=division_reassigned,  # Flag for reassignment
                    is_tied=False,  # Will be updated if tied
                    calculated_at=datetime.utcnow()
                )

                all_division_winners.append(winner)
                tied_participants.append((winner, primary_metric))
                previous_data = participant_data
                winners_created += 1

            # Handle final group of ties for this division
            if len(tied_participants) > 1:
                WinnerService._mark_ties(tied_participants)

            logger.info(f"Created {winners_created} winner(s) for division {division.name} (event {event.id})")

        return all_division_winners

    @staticmethod
    def _sort_scorecards_with_strategy(
        participant_scorecards: List[Dict],
        event: Event,
        config: Optional[WinnerConfiguration] = None
    ) -> List[Dict]:
        """
        Sort participant scorecards using strategy pattern

        Uses scoring-type-specific strategy to:
        - Get primary ranking metric
        - Determine sort order (ascending or descending)
        - Apply tie-breaking rules

        CRITICAL: System 36 and Stableford use DESCENDING sort (higher wins)
                  Stroke and Net use ASCENDING sort (lower wins)

        Args:
            participant_scorecards: List of participant data
            event: Event with scoring type
            config: Optional winner configuration

        Returns:
            Sorted list of participants (best to worst)
        """
        # Get strategy for this scoring type
        strategy = WinnerStrategyFactory.get_strategy(event.scoring_type)

        # Get sort order from strategy
        sort_order = strategy.get_sort_order()

        # Sort using strategy's tie-breaking tuple
        sorted_participants = sorted(
            participant_scorecards,
            key=lambda p_data: strategy.get_tiebreak_tuple(p_data, config),
            reverse=(sort_order == 'desc')  # Descending for points-based scoring
        )

        logger.debug(
            f"Sorted {len(sorted_participants)} participants for {event.scoring_type} "
            f"(order: {sort_order})"
        )

        return sorted_participants

    @staticmethod
    def _check_if_tied(
        data1: Dict,
        data2: Dict,
        event: Event,
        config: Optional[WinnerConfiguration] = None
    ) -> bool:
        """
        Check if two participants are truly tied using strategy pattern

        Two participants are tied if their tie-breaking tuples are identical.
        The strategy defines what constitutes a tie for each scoring type.

        Args:
            data1: First participant data
            data2: Second participant data
            event: Event with scoring type
            config: Winner configuration with tie-breaking method

        Returns:
            True if participants are truly tied, False otherwise
        """
        # Get strategy for this scoring type
        strategy = WinnerStrategyFactory.get_strategy(event.scoring_type)

        # Get tie-breaking tuples from strategy
        tuple1 = strategy.get_tiebreak_tuple(data1, config)
        tuple2 = strategy.get_tiebreak_tuple(data2, config)

        # If tuples are identical, they're truly tied
        return tuple1 == tuple2

    @staticmethod
    def _mark_ties(tied_group: List[Tuple[WinnerResult, int]]):
        """Mark a group of winners as tied"""
        if len(tied_group) <= 1:
            return

        tied_ids = [str(winner.participant_id) for winner, _ in tied_group]

        for winner, score in tied_group:
            winner.is_tied = True
            winner.tied_with = {"participant_ids": tied_ids, "score": score}
            winner.tie_break_criteria = {
                "method": "Tie-breaking applied but players remain tied",
                "note": "All tie-break criteria equal - true tie"
            }

    @staticmethod
    def get_winners(
        session: Session,
        event_id: int,
        division_id: Optional[int] = None,
        top_n: Optional[int] = None
    ) -> List[WinnerResult]:
        """
        Get winner results for an event.

        Returns winners ordered by division (alphabetically) and then by division_rank.

        Args:
            session: Database session
            event_id: Event ID
            division_id: Optional division ID to filter by
            top_n: Optional limit to top N winners per division

        Returns:
            List of WinnerResult objects ordered by division, then division_rank
        """
        query = select(WinnerResult).where(WinnerResult.event_id == event_id)

        if division_id:
            query = query.where(WinnerResult.division_id == division_id)

        # Order by division name first, then by division_rank (1, 2, 3...)
        query = query.order_by(WinnerResult.division, WinnerResult.division_rank)

        if top_n:
            query = query.limit(top_n)

        return list(session.exec(query).all())

    @staticmethod
    def get_overall_winner(session: Session, event_id: int) -> Optional[WinnerResult]:
        """Get the overall winner (rank 1) for an event"""
        winners = WinnerService.get_winners(session, event_id, top_n=1)
        return winners[0] if winners else None

    @staticmethod
    def get_division_winner(
        session: Session, event_id: int, division_id: int
    ) -> Optional[WinnerResult]:
        """Get the winner for a specific division"""
        query = (
            select(WinnerResult)
            .where(WinnerResult.event_id == event_id)
            .where(WinnerResult.division_id == division_id)
            .order_by(WinnerResult.division_rank)
            .limit(1)
        )
        result = session.exec(query).first()
        return result
