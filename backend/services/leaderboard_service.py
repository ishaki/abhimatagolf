from typing import List, Optional, Dict, Any, Tuple
from sqlmodel import Session, select, func, and_, or_
from datetime import datetime, timedelta
from models.event import Event, ScoringType
from models.participant import Participant
from models.scorecard import Scorecard
from models.course import Course, Hole
from models.event_division import EventDivision
from models.leaderboard_cache import LeaderboardCache
from schemas.leaderboard import (
    LeaderboardEntry,
    LeaderboardResponse,
    PublicLeaderboardResponse,
    LeaderboardFilter,
    LeaderboardStats,
    ScoringType as LeaderboardScoringType
)
from services.scoring_strategies import ScoringStrategyFactory
from core.app_logging import logger


class LeaderboardService:
    """Service for leaderboard calculations and caching"""

    def __init__(self, session: Session):
        self.session = session

    def calculate_leaderboard(
        self,
        event_id: int,
        filter_options: Optional[LeaderboardFilter] = None,
        use_cache: bool = True
    ) -> LeaderboardResponse:
        """
        Calculate leaderboard for an event
        
        Args:
            event_id: Event ID
            filter_options: Optional filtering options
            use_cache: Whether to use cached data if available
            
        Returns:
            Complete leaderboard response
        """
        # Check cache first
        if use_cache:
            cached_data = self._get_cached_leaderboard(event_id)
            if cached_data and self._is_cache_valid(cached_data):
                logger.info(f"Using cached leaderboard for event {event_id}")
                return self._build_response_from_cache(cached_data, filter_options)

        # Calculate fresh leaderboard
        logger.info(f"Calculating fresh leaderboard for event {event_id}")
        return self._calculate_fresh_leaderboard(event_id, filter_options)

    def _calculate_fresh_leaderboard(
        self,
        event_id: int,
        filter_options: Optional[LeaderboardFilter] = None
    ) -> LeaderboardResponse:
        """Calculate fresh leaderboard data"""
        
        # Get event details
        event = self.session.get(Event, event_id)
        if not event:
            raise ValueError(f"Event {event_id} not found")

        # Get course details
        course = self.session.get(Course, event.course_id)
        if not course:
            raise ValueError(f"Course {event.course_id} not found")

        # Get all participants for the event
        participants_query = select(Participant).where(Participant.event_id == event_id)
        
        # Apply division filter if specified
        if filter_options and filter_options.division_name:
            participants_query = participants_query.where(
                Participant.division == filter_options.division_name
            )

        participants = self.session.exec(participants_query).all()
        
        # Calculate leaderboard entries
        entries = []
        for participant in participants:
            entry = self._calculate_participant_entry(participant, event, course)
            if entry:
                entries.append(entry)

        # Sort entries based on scoring type
        entries = self._sort_entries(entries, event.scoring_type)

        # Assign ranks
        entries = self._assign_ranks(entries, event.scoring_type)

        # Apply additional filters
        if filter_options:
            entries = self._apply_filters(entries, filter_options)

        # Create response
        response = LeaderboardResponse(
            event_id=event_id,
            event_name=event.name,
            course_name=course.name,
            scoring_type=LeaderboardScoringType(event.scoring_type),
            course_par=self._calculate_course_par(course),
            entries=entries,
            total_participants=len(participants),
            participants_with_scores=len([e for e in entries if e.holes_completed > 0]),
            last_updated=datetime.utcnow()
        )

        # Cache the result
        self._cache_leaderboard(response)

        return response

    def _calculate_participant_entry(
        self,
        participant: Participant,
        event: Event,
        course: Course
    ) -> Optional[LeaderboardEntry]:
        """
        Calculate leaderboard entry for a single participant

        Note: This now reads pre-calculated values from database instead of
        recalculating. All scoring logic happens during score entry (via strategies).
        """

        # Get all scores for this participant
        scores_query = select(Scorecard).where(
            and_(
                Scorecard.participant_id == participant.id,
                Scorecard.strokes > 0
            )
        )
        scores = self.session.exec(scores_query).all()

        if not scores:
            # Participant has no scores yet
            return LeaderboardEntry(
                rank=0,  # Will be assigned later
                participant_id=participant.id,
                participant_name=participant.name,
                handicap=participant.declared_handicap,
                division=participant.division,
                division_id=None,
                gross_score=0,
                net_score=0,
                score_to_par=0,
                holes_completed=0,
                thru="0",
                last_updated=None,
                system36_points=0,
                system36_handicap=0.0
            )

        # Calculate gross score (sum of strokes - this is always needed)
        gross_score = int(sum(score.strokes for score in scores))

        # Read pre-calculated net score (stored by strategy during score entry)
        # Handle None values and ensure integer result
        total_net_score = sum(score.net_score or 0 for score in scores)
        total_net_score = int(total_net_score)

        # Read pre-calculated points (for System36, Stableford, etc.)
        # Handle None values and ensure integer result
        total_points = sum(score.points or 0 for score in scores)
        total_points = int(total_points)

        # Calculate score to par
        course_par = self._calculate_course_par(course)
        score_to_par = int(gross_score - course_par)

        # Determine holes completed
        holes_completed = len(scores)
        thru = self._format_thru(holes_completed)

        # Get last updated time
        last_updated = max(score.updated_at for score in scores) if scores else None

        # For System 36, calculate the System 36 handicap from points
        system36_handicap = 0.0
        if event.scoring_type == ScoringType.SYSTEM_36:
            # Use strategy to calculate System36 handicap
            strategy = ScoringStrategyFactory.get_strategy(event.scoring_type)
            # Classic rule: only compute for full 18 holes
            system36_handicap = strategy.calculate_system36_handicap(total_points, holes_completed)

        return LeaderboardEntry(
            rank=0,  # Will be assigned later
            participant_id=participant.id,
            participant_name=participant.name,
            handicap=participant.declared_handicap,
            division=participant.division,
            division_id=None,
            gross_score=gross_score,
            net_score=total_net_score,
            score_to_par=score_to_par,
            holes_completed=holes_completed,
            thru=thru,
            last_updated=last_updated,
            system36_points=total_points,
            system36_handicap=system36_handicap
        )

    def _sort_entries(self, entries: List[LeaderboardEntry], scoring_type: str) -> List[LeaderboardEntry]:
        """
        Sort entries based on scoring type

        Uses strategy pattern to determine sort key for each scoring type.
        This ensures consistent sorting logic across the application.
        """
        # Get strategy for this scoring type
        strategy = ScoringStrategyFactory.get_strategy(scoring_type)

        # Use strategy's sort key
        return sorted(entries, key=strategy.get_sort_key)

    def _assign_ranks(self, entries: List[LeaderboardEntry], scoring_type: str) -> List[LeaderboardEntry]:
        """
        Assign ranks to entries, handling ties

        Uses strategy pattern to ensure consistent ranking across scoring types.
        Ties are handled by assigning the same rank to entries with identical sort keys.
        """

        if not entries:
            return entries

        # Get strategy for consistent sorting
        strategy = ScoringStrategyFactory.get_strategy(scoring_type)

        # Sort entries using strategy's sort key
        sorted_entries = sorted(entries, key=strategy.get_sort_key)

        # Assign ranks, handling ties
        current_rank = 1
        for i, entry in enumerate(sorted_entries):
            if i > 0:
                # Compare sort keys to detect ties
                prev_key = strategy.get_sort_key(sorted_entries[i-1])
                curr_key = strategy.get_sort_key(entry)

                if curr_key != prev_key:
                    # Not a tie, advance rank
                    current_rank = i + 1

            entry.rank = current_rank

        return sorted_entries

    def _apply_filters(self, entries: List[LeaderboardEntry], filter_options: LeaderboardFilter) -> List[LeaderboardEntry]:
        """Apply additional filters to entries"""
        
        filtered_entries = entries

        # Filter by minimum holes completed
        if filter_options.min_holes:
            filtered_entries = [e for e in filtered_entries if e.holes_completed >= filter_options.min_holes]

        # Filter by maximum rank
        if filter_options.max_rank:
            filtered_entries = [e for e in filtered_entries if e.rank <= filter_options.max_rank]

        return filtered_entries

    def _calculate_course_par(self, course: Course) -> int:
        """Calculate total course par"""
        holes_query = select(Hole).where(Hole.course_id == course.id)
        holes = self.session.exec(holes_query).all()
        return sum(hole.par for hole in holes)

    def _format_thru(self, holes_completed: int) -> str:
        """Format holes completed as 'thru' string"""
        if holes_completed == 0:
            return "0"
        elif holes_completed == 9:
            return "F"
        elif holes_completed == 18:
            return "18"
        else:
            return str(holes_completed)

    def _get_cached_leaderboard(self, event_id: int) -> Optional[LeaderboardCache]:
        """Get cached leaderboard data"""
        cache_query = select(LeaderboardCache).where(LeaderboardCache.event_id == event_id)
        return self.session.exec(cache_query).first()

    def _is_cache_valid(self, cached_data: LeaderboardCache) -> bool:
        """Check if cached data is still valid (30 seconds TTL)"""
        cache_age = datetime.utcnow() - cached_data.last_updated
        return cache_age < timedelta(seconds=30)

    def _build_response_from_cache(
        self,
        cached_data: LeaderboardCache,
        filter_options: Optional[LeaderboardFilter] = None
    ) -> LeaderboardResponse:
        """Build response from cached data"""
        # This would deserialize the cached JSON data
        # For now, we'll recalculate if cache is hit
        return self._calculate_fresh_leaderboard(cached_data.event_id, filter_options)

    def _cache_leaderboard(self, response: LeaderboardResponse) -> None:
        """Cache leaderboard data"""
        try:
            # Check if cache entry exists
            existing_cache = self._get_cached_leaderboard(response.event_id)
            
            # Convert response to dict with proper datetime serialization
            leaderboard_data = response.dict()
            # Convert datetime objects to ISO format strings for JSON serialization
            self._serialize_datetimes(leaderboard_data)
            
            if existing_cache:
                # Update existing cache
                existing_cache.leaderboard_data = leaderboard_data
                existing_cache.last_updated = datetime.utcnow()
            else:
                # Create new cache entry
                cache_entry = LeaderboardCache(
                    event_id=response.event_id,
                    leaderboard_data=leaderboard_data,
                    last_updated=datetime.utcnow()
                )
                self.session.add(cache_entry)
            
            self.session.commit()
            logger.info(f"Cached leaderboard for event {response.event_id}")
            
        except Exception as e:
            logger.error(f"Failed to cache leaderboard: {e}")
            self.session.rollback()

    def _serialize_datetimes(self, data: Dict[str, Any]) -> None:
        """Recursively convert datetime objects to ISO format strings"""
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, datetime):
                    data[key] = value.isoformat()
                elif isinstance(value, dict):
                    self._serialize_datetimes(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            self._serialize_datetimes(item)
                        elif isinstance(item, datetime):
                            # Replace datetime in list
                            index = value.index(item)
                            value[index] = item.isoformat()
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, datetime):
                    data[i] = item.isoformat()
                elif isinstance(item, dict):
                    self._serialize_datetimes(item)

    def invalidate_cache(self, event_id: int) -> None:
        """Invalidate leaderboard cache for an event"""
        try:
            cache_query = select(LeaderboardCache).where(LeaderboardCache.event_id == event_id)
            cached_data = self.session.exec(cache_query).first()
            
            if cached_data:
                self.session.delete(cached_data)
                self.session.commit()
                logger.info(f"Invalidated leaderboard cache for event {event_id}")
                
        except Exception as e:
            logger.error(f"Failed to invalidate cache: {e}")
            self.session.rollback()

    def get_leaderboard_stats(self, event_id: int) -> LeaderboardStats:
        """Get leaderboard statistics"""
        leaderboard = self.calculate_leaderboard(event_id, use_cache=False)
        
        if not leaderboard.entries:
            return LeaderboardStats(
                total_participants=0,
                participants_with_scores=0,
                average_score=0,
                low_score=0,
                high_score=0
            )

        scores = [entry.gross_score for entry in leaderboard.entries if entry.holes_completed > 0]
        
        if not scores:
            return LeaderboardStats(
                total_participants=leaderboard.total_participants,
                participants_with_scores=0,
                average_score=0,
                low_score=0,
                high_score=0
            )

        return LeaderboardStats(
            total_participants=leaderboard.total_participants,
            participants_with_scores=len(scores),
            average_score=sum(scores) / len(scores),
            low_score=min(scores),
            high_score=max(scores),
            leader_margin=scores[1] - scores[0] if len(scores) > 1 else None
        )
