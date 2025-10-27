"""
Net Stroke Play Winner Strategy

Implements winner calculation for net stroke play scoring.
In net stroke play, the player with the lowest net score (gross - course handicap) wins.

Scoring Rules:
- Primary Metric: Net Score (gross score - course handicap)
- Sort Order: Ascending (lower net scores win)
- Tie-Breaking: Standard Golf countback using net scores (back 9, last 6, last 3, last hole)
- Display: Both gross and net scores, course handicap
"""

from typing import Dict, Any, Tuple, Optional
from services.winner_strategies.base import WinnerCalculationStrategy
from models.winner_configuration import TieBreakingMethod


class NetStrokeWinnerStrategy(WinnerCalculationStrategy):
    """
    Winner calculation strategy for Net Stroke Play

    In net stroke play, the winner is the player with the lowest net score.
    Net score = gross score - course handicap (teebox-based).
    Tie-breaking uses standard golf rules applied to net scores.
    """

    def get_primary_metric(self, participant_data: Dict[str, Any]) -> float:
        """
        Return net score as primary ranking metric

        Args:
            participant_data: Dictionary with participant scores

        Returns:
            Net score (lower is better)
            Returns 999 for incomplete/invalid scores
        """
        net_score = participant_data.get('net_score')
        if net_score is None:
            return 999  # Invalid/incomplete - sort to end
        return float(net_score)

    def get_sort_order(self) -> str:
        """
        Return ascending sort order (lower net scores win)

        Returns:
            'asc' for ascending sort
        """
        return 'asc'

    def get_tiebreak_tuple(
        self,
        participant_data: Dict[str, Any],
        config: Optional[Any] = None
    ) -> Tuple:
        """
        Return tuple for tie-breaking using net scores

        Tie-breaking rules (Standard Golf):
        1. Net score (primary)
        2. Back 9 net total (holes 10-18, with handicap strokes)
        3. Last 6 net total (holes 13-18, with handicap strokes)
        4. Last 3 net total (holes 16-18, with handicap strokes)
        5. Last hole net score (hole 18, with handicap strokes)
        6. Declared handicap (if all else equal, lower handicap wins)

        Args:
            participant_data: Dictionary with participant scores
            config: Optional WinnerConfiguration with tie-breaking method

        Returns:
            Tuple for tie-breaking (all values in ascending order)
        """
        net_score = participant_data.get('net_score', 999)

        # Get tie-breaking method from config
        if config:
            method = config.tie_breaking_method
        else:
            method = TieBreakingMethod.STANDARD_GOLF

        # Standard Golf tie-breaking (back 9, last 6, last 3, last hole) - using NET scores
        if method == TieBreakingMethod.STANDARD_GOLF:
            # For net stroke, we use net values for tie-breaking
            # Note: back_nine_total is gross, so we approximate net back 9
            back_nine = participant_data.get('back_nine_total', 999)
            last_6 = participant_data.get('last_6_total', 999)
            last_3 = participant_data.get('last_3_total', 999)
            last_hole = participant_data.get('last_hole_score', 999)
            handicap = participant_data['participant'].declared_handicap
            return (net_score, back_nine, last_6, last_3, last_hole, handicap)

        # Lowest handicap wins ties
        elif method == TieBreakingMethod.LOWEST_HANDICAP:
            handicap = participant_data['participant'].declared_handicap
            return (net_score, handicap)

        # Share position - all tied players get same rank
        elif method == TieBreakingMethod.SHARE_POSITION:
            return (net_score, 0)  # Secondary value doesn't matter

        # Other methods - just use primary score
        else:
            return (net_score, 0)

    def is_eligible(
        self,
        participant_data: Dict[str, Any],
        config: Optional[Any] = None
    ) -> bool:
        """
        Check if participant is eligible for winner calculation

        Eligibility based on configuration:
        - If exclude_incomplete_rounds: must have minimum holes
        - Otherwise: just needs to have played at least one hole
        - Must have a valid net score (gross score and handicap)

        Args:
            participant_data: Dictionary with participant scores
            config: Optional WinnerConfiguration with eligibility rules

        Returns:
            True if eligible, False otherwise
        """
        holes_completed = participant_data.get('holes_completed', 0)
        net_score = participant_data.get('net_score')

        # Must have valid net score
        if net_score is None:
            return False

        if config and config.exclude_incomplete_rounds:
            return holes_completed >= config.minimum_holes_for_ranking

        # At least one hole must be completed
        return holes_completed > 0

    def prepare_winner_display_data(self, participant_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare display data for net stroke play winner

        Net stroke play shows:
        - Net score (primary metric)
        - Gross score
        - Course handicap (used for net calculation)
        - Declared handicap

        Args:
            participant_data: Dictionary with all participant scores

        Returns:
            Dictionary with net stroke play display data
        """
        participant = participant_data['participant']
        return {
            'net_score': participant_data.get('net_score'),
            'gross_score': participant_data.get('gross_score', 0),
            'course_handicap': participant.course_handicap,
            'declared_handicap': participant.declared_handicap,
        }

    def get_display_metric_name(self) -> str:
        """
        Return human-readable name for primary metric

        Returns:
            "Net Score" for net stroke play
        """
        return "Net Score"

    def supports_special_awards(self) -> bool:
        """
        Net stroke play supports both Best Gross and Best Net awards

        Returns:
            True
        """
        return True
