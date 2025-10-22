"""
Winner Service - Calculate tournament winners with tie-breaking

This service calculates winners for golf tournaments, handling:
- Overall winners
- Division winners
- Tie-breaking using standard golf rules
"""

from typing import List, Dict, Any, Optional, Tuple
from sqlmodel import Session, select
from models.winner_result import WinnerResult
from models.event import Event, ScoringType
from models.participant import Participant
from models.scorecard import Scorecard
from models.event_division import EventDivision
from datetime import datetime
from core.app_logging import logger


class WinnerService:
    """Service for calculating and managing tournament winners"""

    @staticmethod
    def calculate_winners(session: Session, event_id: int) -> List[WinnerResult]:
        """
        Calculate winners for an event with proper tie-breaking.

        Args:
            session: Database session
            event_id: Event ID to calculate winners for

        Returns:
            List of WinnerResult objects

        Raises:
            ValueError: If event not found or has no scorecards
        """
        # Get event
        event = session.get(Event, event_id)
        if not event:
            raise ValueError(f"Event {event_id} not found")

        # Get all participants for the event
        participants_query = select(Participant).where(Participant.event_id == event_id)
        participants = list(session.exec(participants_query).all())

        if not participants:
            raise ValueError(f"No participants found for event {event_id}")

        # Clear existing winner results
        WinnerService._clear_existing_winners(session, event_id)

        # Build participant scorecards with totals
        participant_scorecards = WinnerService._build_participant_scorecards(session, event, participants)

        # Calculate overall winners
        overall_winners = WinnerService._calculate_overall_winners(
            session, event, participant_scorecards
        )

        # Calculate division winners if divisions exist
        division_winners = WinnerService._calculate_division_winners(
            session, event, participant_scorecards
        )

        # Combine and save results
        all_winners = overall_winners + division_winners
        for winner in all_winners:
            session.add(winner)

        session.commit()
        logger.info(f"Calculated {len(all_winners)} winner results for event {event_id}")

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
            
            participant_data = {
                'participant': participant,
                'gross_score': gross_score if holes_completed > 0 else None,
                'net_score': net_score,
                'front_nine_total': front_nine_total,
                'back_nine_total': back_nine_total,
                'last_6_total': last_6_total,
                'last_3_total': last_3_total,
                'last_hole_score': last_hole_score,
                'holes_completed': holes_completed
            }
            
            participant_scorecards.append(participant_data)
        
        return participant_scorecards

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
        session: Session, event: Event, participant_scorecards: List[Dict]
    ) -> List[WinnerResult]:
        """Calculate overall event winners"""
        winners = []

        # Determine which score to use based on scoring type
        use_net = event.scoring_type in [ScoringType.NET_STROKE, ScoringType.SYSTEM_36]

        # Sort participant scorecards by score with tie-breaking
        sorted_participants = WinnerService._sort_scorecards_with_tiebreak(
            participant_scorecards, use_net
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
                handicap=participant.course_handicap,
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
        session: Session, event: Event, participant_scorecards: List[Dict]
    ) -> List[WinnerResult]:
        """Calculate division-specific winners"""
        # Get divisions for the event
        divisions_query = select(EventDivision).where(EventDivision.event_id == event.id)
        divisions = list(session.exec(divisions_query).all())

        if not divisions:
            return []

        all_division_winners = []
        use_net = event.scoring_type in [ScoringType.NET_STROKE, ScoringType.SYSTEM_36]

        for division in divisions:
            # Filter participant scorecards by division
            division_participants = [
                p_data for p_data in participant_scorecards
                if p_data['participant'].division_id == division.id
            ]

            if not division_participants:
                continue

            # Sort division participants
            sorted_participants = WinnerService._sort_scorecards_with_tiebreak(
                division_participants, use_net
            )

            # Assign division ranks
            for idx, participant_data in enumerate(sorted_participants):
                participant = participant_data['participant']

                # Find the overall winner result to update division rank
                overall_winner = next(
                    (w for w in all_division_winners if w.participant_id == participant.id),
                    None
                )

                if overall_winner:
                    overall_winner.division_rank = idx + 1

        return []  # Division ranks are updated in overall_winners

    @staticmethod
    def _sort_scorecards_with_tiebreak(
        participant_scorecards: List[Dict], use_net: bool
    ) -> List[Dict]:
        """
        Sort participant scorecards by score with tie-breaking rules.

        Tie-breaking order:
        1. Primary score (gross or net)
        2. Back 9 score (lower is better)
        3. Last 6 holes score
        4. Last 3 holes score
        5. Last hole score
        """
        def get_tiebreak_scores(participant_data: Dict) -> Tuple:
            """Get tuple of scores for tie-breaking"""
            primary_score = participant_data['net_score'] if use_net else participant_data['gross_score']
            if primary_score is None:
                primary_score = 999  # Put incomplete rounds at the end

            # Calculate back 9 score (holes 10-18)
            back_nine_score = participant_data.get('back_nine_total', 999)

            # Calculate last 6 holes (13-18)
            last_6_score = participant_data.get('last_6_total', 999)

            # Calculate last 3 holes (16-18)
            last_3_score = participant_data.get('last_3_total', 999)

            # Last hole
            last_hole_score = participant_data.get('last_hole_score', 999)

            return (primary_score, back_nine_score, last_6_score, last_3_score, last_hole_score)

        return sorted(participant_scorecards, key=get_tiebreak_scores)

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
                "method": "Standard golf tie-breaking (back 9, last 6, last 3, last hole)",
                "note": "All players tied with same score after tie-breaking"
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

        Args:
            session: Database session
            event_id: Event ID
            division_id: Optional division ID to filter by
            top_n: Optional limit to top N winners

        Returns:
            List of WinnerResult objects
        """
        query = select(WinnerResult).where(WinnerResult.event_id == event_id)

        if division_id:
            query = query.where(WinnerResult.division_id == division_id)

        query = query.order_by(WinnerResult.overall_rank)

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
