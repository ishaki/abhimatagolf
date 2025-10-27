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

        # Calculate division winners (this is the primary calculation)
        division_winners = WinnerService._calculate_division_winners(
            session, event, participant_scorecards, config
        )

        # For System 36 Standard and Stableford, create auto-assigned sub-divisions if configured
        if config and config.subdivision_ranges and WinnerService._needs_auto_subdivisions(event):
            logger.info(f"Processing auto-assigned sub-divisions for event {event_id}")
            sub_division_winners = WinnerService._create_auto_subdivision_winners(
                session, event, division_winners, config
            )
            division_winners.extend(sub_division_winners)

        # Save all winner results
        for winner in division_winners:
            session.add(winner)

        session.commit()
        logger.info(f"Calculated {len(division_winners)} winner results for event {event_id}")

        return division_winners

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
            # Filter participant scorecards by division
            division_participants = [
                p_data for p_data in participant_scorecards
                if p_data['participant'].division_id == division.id
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

    # ==================== SUB-DIVISION SUPPORT ====================

    @staticmethod
    def _needs_auto_subdivisions(event: Event) -> bool:
        """
        Determine if event scoring type requires auto-assigned sub-divisions.

        Returns True for:
        - System 36 Standard (handicap calculated from scores)
        - Stableford (future support)
        """
        return (
            event.scoring_type == ScoringType.SYSTEM_36 and
            event.system36_variant == System36Variant.STANDARD
        ) or event.scoring_type == ScoringType.STABLEFORD

    @staticmethod
    def _create_auto_subdivision_winners(
        session: Session,
        event: Event,
        division_winners: List[WinnerResult],
        config: WinnerConfiguration
    ) -> List[WinnerResult]:
        """
        Create auto-assigned sub-divisions and winners based on subdivision_ranges.

        For System 36 Standard and Stableford:
        1. Takes winners from parent divisions (e.g., Men)
        2. Groups them by handicap ranges defined in config.subdivision_ranges
        3. Creates auto-assigned sub-divisions (e.g., Men A, Men B, Men C)
        4. Creates WinnerResult records for each sub-division group

        Args:
            session: Database session
            event: Event
            division_winners: List of winners from parent divisions
            config: Winner configuration with subdivision_ranges

        Returns:
            List of new WinnerResult objects for sub-divisions
        """
        from services.event_division_service import EventDivisionService

        if not config.subdivision_ranges:
            return []

        division_service = EventDivisionService(session)
        sub_division_winners = []

        # Parse subdivision_ranges: {"Men": {"A": [0, 12], "B": [13, 20], "C": [21, 36]}}
        for parent_division_name, sub_ranges in config.subdivision_ranges.items():
            # Get parent division
            parent_division_query = select(EventDivision).where(
                EventDivision.event_id == event.id,
                EventDivision.name == parent_division_name,
                EventDivision.parent_division_id.is_(None)  # Ensure it's a parent
            )
            parent_division = session.exec(parent_division_query).first()

            if not parent_division:
                logger.warning(f"Parent division '{parent_division_name}' not found for event {event.id}")
                continue

            # Get winners from this parent division
            parent_winners = [
                w for w in division_winners
                if w.division_id == parent_division.id
            ]

            if not parent_winners:
                logger.info(f"No winners in parent division '{parent_division_name}' to subdivide")
                continue

            # Create or get auto-assigned sub-divisions
            subdivisions_map = {}
            for sub_name, (handicap_min, handicap_max) in sub_ranges.items():
                full_subdivision_name = f"{parent_division_name} {sub_name}"

                # Check if sub-division already exists
                existing_subdivision = session.exec(
                    select(EventDivision).where(
                        EventDivision.event_id == event.id,
                        EventDivision.name == full_subdivision_name,
                        EventDivision.parent_division_id == parent_division.id
                    )
                ).first()

                if existing_subdivision:
                    # Update handicap ranges if changed
                    existing_subdivision.handicap_min = float(handicap_min)
                    existing_subdivision.handicap_max = float(handicap_max)
                    existing_subdivision.is_auto_assigned = True
                    session.add(existing_subdivision)
                    subdivisions_map[sub_name] = existing_subdivision
                else:
                    # Create new auto-assigned sub-division
                    subdivision = division_service.create_auto_subdivision(
                        parent_division_id=parent_division.id,
                        name=full_subdivision_name,
                        handicap_min=float(handicap_min),
                        handicap_max=float(handicap_max)
                    )
                    subdivisions_map[sub_name] = subdivision

            # Group winners by handicap into sub-divisions
            for sub_name, subdivision in subdivisions_map.items():
                # Filter winners that fall into this handicap range
                sub_winners = []
                for winner in parent_winners:
                    # Use calculated handicap for System 36, declared for others
                    handicap_to_use = (
                        winner.system36_handicap if event.scoring_type == ScoringType.SYSTEM_36
                        else winner.declared_handicap
                    )

                    if handicap_to_use is None:
                        continue

                    if subdivision.handicap_min <= handicap_to_use <= subdivision.handicap_max:
                        sub_winners.append(winner)

                if not sub_winners:
                    logger.info(f"No winners in sub-division '{subdivision.name}'")
                    continue

                # Sort sub_winners by division_rank (already calculated in parent)
                sub_winners.sort(key=lambda w: w.division_rank)

                # Create WinnerResult for each winner in this sub-division
                for rank, parent_winner in enumerate(sub_winners, start=1):
                    sub_winner = WinnerResult(
                        event_id=event.id,
                        participant_id=parent_winner.participant_id,
                        participant_name=parent_winner.participant_name,
                        division=subdivision.name,
                        division_id=subdivision.id,
                        overall_rank=None,
                        division_rank=rank,  # Rank within sub-division
                        gross_score=parent_winner.gross_score,
                        net_score=parent_winner.net_score,
                        declared_handicap=parent_winner.declared_handicap,
                        course_handicap=parent_winner.course_handicap,
                        system36_handicap=parent_winner.system36_handicap,
                        teebox_name=parent_winner.teebox_name,
                        teebox_course_rating=parent_winner.teebox_course_rating,
                        teebox_slope_rating=parent_winner.teebox_slope_rating,
                        is_tied=parent_winner.is_tied,  # Preserve tie status
                        calculated_at=datetime.utcnow()
                    )
                    sub_division_winners.append(sub_winner)

                logger.info(f"Created {len(sub_winners)} winner(s) for sub-division '{subdivision.name}'")

        return sub_division_winners
