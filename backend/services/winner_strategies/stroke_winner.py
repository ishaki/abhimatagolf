"""
Stroke Play Winner Strategy

Implements winner calculation for gross stroke play scoring.
In stroke play, the player with the lowest total gross score wins.

Scoring Rules:
- Primary Metric: Gross Score (sum of all strokes)
- Sort Order: Ascending (lower scores win)
- Tie-Breaking: Standard Golf countback (back 9, last 6, last 3, last hole)
- Display: Gross score only
"""

from typing import Dict, Any, Tuple, Optional
from services.winner_strategies.base import WinnerCalculationStrategy
from models.winner_configuration import TieBreakingMethod


class StrokeWinnerStrategy(WinnerCalculationStrategy):
    """
    Winner calculation strategy for Stroke Play (gross scoring)

    In stroke play, the winner is the player with the lowest gross score.
    Tie-breaking uses standard golf rules: back 9, last 6, last 3, last hole.
    """

    def get_primary_metric(self, participant_data: Dict[str, Any]) -> float:
        """
        Return gross score as primary ranking metric

        Args:
            participant_data: Dictionary with participant scores

        Returns:
            Gross score (lower is better)
            Returns 999 for incomplete/invalid scores
        """
        gross_score = participant_data.get('gross_score')
        if gross_score is None or gross_score <= 0:
            return 999  # Invalid/incomplete - sort to end
        return float(gross_score)

    def get_sort_order(self) -> str:
        """
        Return ascending sort order (lower gross scores win)

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
        Return tuple for tie-breaking using gross scores

        Tie-breaking rules (Standard Golf):
        1. Gross score (primary)
        2. Back 9 gross total (holes 10-18)
        3. Last 6 gross total (holes 13-18)
        4. Last 3 gross total (holes 16-18)
        5. Last hole gross score (hole 18)

        Args:
            participant_data: Dictionary with participant scores
            config: Optional WinnerConfiguration with tie-breaking method

        Returns:
            Tuple for tie-breaking (all values in ascending order)
        """
        gross_score = participant_data.get('gross_score', 999)

        # Get tie-breaking method from config
        if config:
            method = config.tie_breaking_method
        else:
            method = TieBreakingMethod.STANDARD_GOLF

        # Standard Golf tie-breaking (back 9, last 6, last 3, last hole)
        if method == TieBreakingMethod.STANDARD_GOLF:
            back_nine = participant_data.get('back_nine_total', 999)
            last_6 = participant_data.get('last_6_total', 999)
            last_3 = participant_data.get('last_3_total', 999)
            last_hole = participant_data.get('last_hole_score', 999)
            return (gross_score, back_nine, last_6, last_3, last_hole)

        # Lowest handicap wins ties
        elif method == TieBreakingMethod.LOWEST_HANDICAP:
            handicap = participant_data['participant'].declared_handicap
            return (gross_score, handicap)

        # Share position - all tied players get same rank
        elif method == TieBreakingMethod.SHARE_POSITION:
            return (gross_score, 0)  # Secondary value doesn't matter

        # Other methods - just use primary score
        else:
            return (gross_score, 0)

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

        Args:
            participant_data: Dictionary with participant scores
            config: Optional WinnerConfiguration with eligibility rules

        Returns:
            True if eligible, False otherwise
        """
        holes_completed = participant_data.get('holes_completed', 0)

        if config and config.exclude_incomplete_rounds:
            return holes_completed >= config.minimum_holes_for_ranking

        # At least one hole must be completed
        return holes_completed > 0

    def prepare_winner_display_data(self, participant_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare display data for stroke play winner

        Stroke play shows:
        - Gross score (primary metric)

        Args:
            participant_data: Dictionary with all participant scores

        Returns:
            Dictionary with stroke play display data
        """
        return {
            'gross_score': participant_data.get('gross_score', 0),
        }

    def get_display_metric_name(self) -> str:
        """
        Return human-readable name for primary metric

        Returns:
            "Gross Score" for stroke play
        """
        return "Gross Score"

    def supports_special_awards(self) -> bool:
        """
        Stroke play supports Best Gross award

        Returns:
            True
        """
        return True
