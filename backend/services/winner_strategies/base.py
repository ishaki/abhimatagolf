"""
Base Winner Calculation Strategy

Abstract base class defining the interface for all winner calculation strategies.
Each scoring type (Stroke, Net Stroke, System 36, Stableford) implements this
interface to provide scoring-type-specific winner calculation logic.

The Strategy Pattern allows us to:
1. Separate winner calculation logic per scoring type
2. Use correct sort order (ascending for stroke, descending for points)
3. Apply scoring-type-specific tie-breaking rules
4. Easily add new scoring types without modifying existing code
5. Test each strategy independently
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, Optional


class WinnerCalculationStrategy(ABC):
    """
    Abstract base class for all winner calculation strategies

    Each concrete strategy must implement:
    - get_primary_metric(): Return the score/metric used for ranking
    - get_sort_order(): Return 'asc' or 'desc' for sort direction
    - get_tiebreak_tuple(): Return tuple for tie-breaking
    - is_eligible(): Check if participant qualifies for winner calculation
    - prepare_winner_display_data(): Format scoring-specific display data
    """

    @abstractmethod
    def get_primary_metric(self, participant_data: Dict[str, Any]) -> float:
        """
        Return the primary score/metric used for ranking

        This is the main value used to determine winner order.
        Different scoring types use different metrics:
        - Stroke Play: gross_score
        - Net Stroke: net_score
        - System 36: system36_points
        - Stableford: stableford_points

        Args:
            participant_data: Dictionary containing participant scores and metadata
                Expected keys: 'participant', 'gross_score', 'net_score',
                              'system36_points', 'holes_completed', etc.

        Returns:
            Primary metric value for ranking (float)
            Returns 999 for incomplete/invalid scores (sorted to end)

        Example:
            For Stroke Play:
                return participant_data.get('gross_score', 999)

            For System 36:
                return participant_data.get('system36_points', 0)
        """
        pass

    @abstractmethod
    def get_sort_order(self) -> str:
        """
        Return sort order for ranking

        Different scoring types use different sort orders:
        - Stroke/Net Stroke: 'asc' (lower scores win)
        - System 36/Stableford: 'desc' (higher points win)

        Returns:
            'asc' for ascending (lower is better) or
            'desc' for descending (higher is better)

        Example:
            Stroke Play:
                return 'asc'  # Lower gross score wins

            System 36:
                return 'desc'  # Higher points win
        """
        pass

    @abstractmethod
    def get_tiebreak_tuple(
        self,
        participant_data: Dict[str, Any],
        config: Optional[Any] = None
    ) -> Tuple:
        """
        Return tuple of values for tie-breaking

        When participants have the same primary metric, this tuple
        determines the order. Python sorts tuples element by element.

        Tie-breaking rules vary by scoring type:
        - Stroke/Net: Back 9, Last 6, Last 3, Last Hole (lower wins)
        - System 36: Back 9 points, calculated handicap (higher points, lower handicap)
        - Stableford: Back 9 points, Last 6 points (higher wins)

        Args:
            participant_data: Dictionary with participant scores
            config: Optional WinnerConfiguration with tie-breaking method

        Returns:
            Tuple of comparable values for tie-breaking
            First element is primary metric, followed by tie-break criteria

        Example:
            For Stroke Play with Standard Golf tie-breaking:
                gross = participant_data.get('gross_score', 999)
                back_9 = participant_data.get('back_nine_total', 999)
                last_6 = participant_data.get('last_6_total', 999)
                last_3 = participant_data.get('last_3_total', 999)
                last_hole = participant_data.get('last_hole_score', 999)
                return (gross, back_9, last_6, last_3, last_hole)

            For System 36 (note: negate for descending sort):
                points = participant_data.get('system36_points', 0)
                back_9_pts = participant_data.get('back_nine_points', 0)
                handicap = participant_data.get('calculated_handicap', 999)
                return (-points, -back_9_pts, handicap)
        """
        pass

    @abstractmethod
    def is_eligible(
        self,
        participant_data: Dict[str, Any],
        config: Optional[Any] = None
    ) -> bool:
        """
        Check if participant is eligible for winner calculation

        Eligibility rules vary by scoring type and configuration:
        - Minimum holes completed (e.g., 18 for full round)
        - System 36 requires 18 holes to calculate handicap
        - May exclude incomplete rounds based on config

        Args:
            participant_data: Dictionary with participant scores and metadata
            config: Optional WinnerConfiguration with eligibility rules

        Returns:
            True if participant is eligible, False otherwise

        Example:
            For Stroke Play:
                holes_completed = participant_data.get('holes_completed', 0)
                if config and config.exclude_incomplete_rounds:
                    return holes_completed >= config.minimum_holes_for_ranking
                return holes_completed > 0

            For System 36 (requires full 18 holes):
                holes_completed = participant_data.get('holes_completed', 0)
                return holes_completed >= 18
        """
        pass

    @abstractmethod
    def prepare_winner_display_data(self, participant_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare scoring-type-specific display data for winner result

        Different scoring types show different information:
        - Stroke: gross_score
        - Net Stroke: gross_score, net_score, course_handicap
        - System 36: system36_points, calculated_handicap, net_score, gross_score
        - Stableford: stableford_points, gross_score, net_score

        Args:
            participant_data: Dictionary with all participant scores

        Returns:
            Dictionary with scoring-specific display data
            This data is stored in WinnerResult for display

        Example:
            For Stroke Play:
                return {
                    'gross_score': participant_data.get('gross_score', 0),
                }

            For System 36:
                return {
                    'system36_points': participant_data.get('system36_points', 0),
                    'calculated_handicap': participant_data.get('calculated_handicap'),
                    'net_score': participant_data.get('net_score'),
                    'gross_score': participant_data.get('gross_score', 0),
                }
        """
        pass

    def get_display_metric_name(self) -> str:
        """
        Return human-readable name for primary metric

        Optional method for UI display purposes.

        Returns:
            Name of the primary metric (e.g., "Gross Score", "Total Points")

        Example:
            Stroke Play: return "Gross Score"
            System 36: return "Total Points"
        """
        return "Score"

    def supports_special_awards(self) -> bool:
        """
        Return whether this scoring type supports special awards

        Some scoring types may not support certain special awards.
        For example, gross-only scoring may not have "Best Net" award.

        Returns:
            True if special awards (best gross/net) are meaningful

        Example:
            Stroke Play: return True  # Can have best gross
            Net Stroke: return True   # Can have both best gross and best net
        """
        return True
