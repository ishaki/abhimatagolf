"""
Live Score Service - Phase 3.2

Provides public API for real-time score display on TV/projector.
Returns raw scorecard data without calculations for all participants.
"""

from typing import List, Optional
from sqlmodel import Session, select
from datetime import datetime, timedelta
from models.participant import Participant
from models.event import Event
from models.scorecard import Scorecard
from models.course import Hole
from schemas.scorecard import ScorecardResponse, HoleScoreResponse
from fastapi import HTTPException, status


class LiveScoreService:
    """
    Service for Live Score Display (Phase 3.2)

    Provides public access to raw scorecard data for tournament display.
    Implements smart sorting and caching for performance.
    """

    def __init__(self, session: Session):
        self.session = session
        self._cache = {}  # Simple in-memory cache
        self._cache_ttl = 30  # seconds

    def get_live_score(
        self,
        event_id: int,
        sort_by: str = "gross"
    ) -> List[ScorecardResponse]:
        """
        Get live score data for all participants in an event

        Args:
            event_id: ID of the event
            sort_by: Sort method - "gross" or "net" (default: "gross")
                     Note: In Phase 3, both sort the same way (by gross)
                     Net sorting will be enabled after Winner Page calculations

        Returns:
            List of ScorecardResponse for all participants, sorted by:
            1. Holes completed (descending)
            2. Gross score (ascending - lowest first)
            3. Participants with zero scores at bottom
        """
        # Check cache first
        cache_key = f"live_score_{event_id}_{sort_by}"
        if cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if datetime.utcnow() - cached_time < timedelta(seconds=self._cache_ttl):
                return cached_data

        # Get event
        event = self.session.get(Event, event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event {event_id} not found"
            )

        # Get all participants for this event
        participants_stmt = select(Participant).where(
            Participant.event_id == event_id
        )
        participants = self.session.exec(participants_stmt).all()

        # Build scorecard responses for all participants
        scorecards = []
        for participant in participants:
            scorecard = self._build_participant_scorecard(participant, event)
            scorecards.append(scorecard)

        # Sort scorecards using smart sorting logic
        sorted_scorecards = self._sort_scorecards(scorecards)

        # Cache the results
        self._cache[cache_key] = (sorted_scorecards, datetime.utcnow())

        return sorted_scorecards

    def _build_participant_scorecard(
        self,
        participant: Participant,
        event: Event
    ) -> ScorecardResponse:
        """
        Build scorecard response for a single participant

        Similar to ScorecardService.get_participant_scorecard() but optimized
        for live score display (no unnecessary calculations)
        """
        # Get all scorecards for this participant
        scorecards_stmt = select(Scorecard).where(
            Scorecard.participant_id == participant.id
        )
        scorecards = self.session.exec(scorecards_stmt).all()

        # Get all holes for the course
        holes_stmt = select(Hole).where(
            Hole.course_id == event.course_id
        ).order_by(Hole.number)
        holes = self.session.exec(holes_stmt).all()

        # Create hole mapping
        scorecard_map = {sc.hole_id: sc for sc in scorecards}

        # Build front nine and back nine
        front_nine = []
        back_nine = []
        out_total = 0
        in_total = 0
        out_par = 0
        in_par = 0
        holes_completed = 0

        for hole in holes:
            scorecard = scorecard_map.get(hole.id)
            strokes = scorecard.strokes if scorecard else 0

            if strokes > 0:
                holes_completed += 1

            score_to_par = (strokes - hole.par) if strokes > 0 else 0
            color_code = self._get_color_code(score_to_par) if strokes > 0 else "none"

            hole_response = HoleScoreResponse(
                id=scorecard.id if scorecard else 0,
                hole_number=hole.number,
                hole_par=hole.par,
                hole_distance=hole.distance_meters or 0,
                handicap_index=hole.handicap_index,
                strokes=strokes,
                score_to_par=score_to_par,
                color_code=color_code,
                system36_points=None,  # Phase 3: No calculations
            )

            if hole.number <= 9:
                front_nine.append(hole_response)
                out_total += strokes
                out_par += hole.par
            else:
                back_nine.append(hole_response)
                in_total += strokes
                in_par += hole.par

        # Calculate basic totals
        gross_score = out_total + in_total
        course_par = out_par + in_par
        score_to_par = (gross_score - course_par) if gross_score > 0 else 0
        out_to_par = (out_total - out_par) if out_total > 0 else 0
        in_to_par = (in_total - in_par) if in_total > 0 else 0

        return ScorecardResponse(
            participant_id=participant.id,
            participant_name=participant.name,
            event_id=event.id,
            event_name=event.name,
            handicap=participant.declared_handicap,
            front_nine=front_nine,
            out_total=out_total,
            out_to_par=out_to_par,
            back_nine=back_nine,
            in_total=in_total,
            in_to_par=in_to_par,
            gross_score=gross_score,
            net_score=0,  # Phase 3: No net calculations
            score_to_par=score_to_par,
            course_par=course_par,
            holes_completed=holes_completed,
            last_updated=None,
            recorded_by=None,
            system36_points=None,
        )

    def _sort_scorecards(self, scorecards: List[ScorecardResponse]) -> List[ScorecardResponse]:
        """
        Sort scorecards using smart sorting logic:
        1. Holes completed (descending) - most holes first
        2. Gross score (ascending) - lowest score first
        3. Participants with zero scores at bottom
        """
        def sort_key(scorecard: ScorecardResponse):
            # Participants with no scores go to the bottom
            if scorecard.holes_completed == 0:
                return (1, 0, 999999)  # (has_scores, -holes_completed, gross)

            # Participants with scores sorted by holes completed, then gross
            return (0, -scorecard.holes_completed, scorecard.gross_score)

        return sorted(scorecards, key=sort_key)

    def _get_color_code(self, score_to_par: int) -> str:
        """Get color code based on score relative to par"""
        if score_to_par <= -2:
            return "eagle"
        elif score_to_par == -1:
            return "birdie"
        elif score_to_par == 0:
            return "par"
        elif score_to_par == 1:
            return "bogey"
        else:
            return "double_bogey"

    def invalidate_cache(self, event_id: int):
        """
        Invalidate cache for an event (called when scores are updated)
        """
        # Remove all cache entries for this event
        keys_to_remove = [k for k in self._cache.keys() if k.startswith(f"live_score_{event_id}_")]
        for key in keys_to_remove:
            del self._cache[key]
