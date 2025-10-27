"""
System 36 Winner Strategy

Implements winner calculation for System 36 scoring.
In System 36, the player with the LOWEST net score wins.

System 36 Scoring Rules:
- Points per hole based on GROSS score vs par:
  * Par or better (≤0): 2 points
  * Bogey (+1): 1 point
  * Double bogey or worse (≥+2): 0 points
- System 36 Handicap = 36 - Total Points (18 holes only)
- Net Score = Gross Score - System 36 Handicap
- Lower net score wins (ASCENDING sort order)

Scoring Rules:
- Primary Metric: Net Score (gross - System 36 handicap)
- Sort Order: ASCENDING (lower net score wins)
- Tie-Breaking: GROSS scores (back 9, last 6, last 3, last hole) following configuration
- Display: Net score (primary), with points visible in Excel export
- Eligibility: Must complete 18 holes to calculate System 36 handicap
"""

from typing import Dict, Any, Tuple, Optional
from services.winner_strategies.base import WinnerCalculationStrategy
from models.winner_configuration import TieBreakingMethod


class System36WinnerStrategy(WinnerCalculationStrategy):
    """
    Winner calculation strategy for System 36 scoring

    In System 36, the winner is the player with the LOWEST net score.
    Net Score = Gross Score - System 36 Handicap (36 - total points).
    This is similar to net stroke play.

    IMPORTANT: Sort order is ASCENDING (lower net score wins)
    """

    def get_primary_metric(self, participant_data: Dict[str, Any]) -> float:
        """
        Return net score as primary ranking metric

        Args:
            participant_data: Dictionary with participant scores

        Returns:
            Net score (gross - System 36 handicap) - lower is better
            Returns 999 for incomplete/invalid scores (sorted to end with ascending)
        """
        # Net score = Gross - System 36 Handicap
        # System 36 Handicap = 36 - Total Points (calculated in winner_service)
        net_score = participant_data.get('net_score')

        if net_score is None:
            return 999  # Invalid/incomplete - sort to end

        return float(net_score)

    def get_sort_order(self) -> str:
        """
        Return ASCENDING sort order (lower net score wins)

        CRITICAL: System 36 uses net score - lower net score wins!
        This is similar to net stroke play.

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
        Return tuple for tie-breaking using System 36 rules

        Tie-breaking rules for System 36:
        1. Net score (primary) - LOWER wins
        2. Back 9 GROSS total - LOWER wins
        3. Last 6 GROSS total - LOWER wins
        4. Last 3 GROSS total - LOWER wins
        5. Last hole GROSS score - LOWER wins
        6. Declared handicap - LOWER wins

        NOTE: For ascending sort, all values are positive (lower wins naturally)

        Args:
            participant_data: Dictionary with participant scores
            config: Optional WinnerConfiguration with tie-breaking method

        Returns:
            Tuple for tie-breaking using GROSS scores
            All values positive for ascending sort (lower wins)
        """
        net_score = participant_data.get('net_score', 999)

        # Get tie-breaking method from config
        if config:
            method = config.tie_breaking_method
        else:
            method = TieBreakingMethod.STANDARD_GOLF

        # Standard Golf tie-breaking using GROSS scores (back 9, last 6, last 3, last hole)
        if method == TieBreakingMethod.STANDARD_GOLF:
            # Use GROSS scores for tie-breaking (standard golf rules)
            back_nine = participant_data.get('back_nine_total', 999)  # GROSS back 9
            last_6 = participant_data.get('last_6_total', 999)       # GROSS last 6
            last_3 = participant_data.get('last_3_total', 999)       # GROSS last 3
            last_hole = participant_data.get('last_hole_score', 999) # GROSS last hole
            declared_handicap = participant_data['participant'].declared_handicap

            # Tuple: lower net first, then lower back 9, then lower last 6, etc.
            # For ascending sort: all values positive (lower wins naturally)
            return (net_score, back_nine, last_6, last_3, last_hole, declared_handicap)

        # Lowest handicap wins ties
        elif method == TieBreakingMethod.LOWEST_HANDICAP:
            declared_handicap = participant_data['participant'].declared_handicap
            # For ascending sort: all positive (lower wins)
            return (net_score, declared_handicap)

        # Share position - all tied players get same rank
        elif method == TieBreakingMethod.SHARE_POSITION:
            return (net_score, 0)  # Secondary value doesn't matter

        # Other methods - just use primary metric
        else:
            return (net_score, 0)

    def is_eligible(
        self,
        participant_data: Dict[str, Any],
        config: Optional[Any] = None
    ) -> bool:
        """
        Check if participant is eligible for System 36 winner calculation

        System 36 Eligibility:
        - MUST complete full 18 holes to calculate System 36 handicap
        - This is a hard requirement for System 36 scoring

        Args:
            participant_data: Dictionary with participant scores
            config: Optional WinnerConfiguration (eligibility rules)

        Returns:
            True if eligible (18 holes completed), False otherwise
        """
        holes_completed = participant_data.get('holes_completed', 0)

        # System 36 requires full 18 holes to calculate handicap
        # This overrides config settings
        return holes_completed >= 18

    def prepare_winner_display_data(self, participant_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare display data for System 36 winner

        System 36 shows:
        - Net score (primary metric) - gross - calculated handicap
        - Gross score
        - Calculated handicap (36 - total points)
        - Total points (available in Excel export)

        Args:
            participant_data: Dictionary with all participant scores

        Returns:
            Dictionary with System 36 display data
        """
        return {
            'system36_points': participant_data.get('system36_points', 0),
            'calculated_handicap': participant_data.get('calculated_handicap'),
            'net_score': participant_data.get('net_score'),
            'gross_score': participant_data.get('gross_score', 0),
        }

    def get_display_metric_name(self) -> str:
        """
        Return human-readable name for primary metric

        Returns:
            "Net Score" for System 36
        """
        return "Net Score"

    def supports_special_awards(self) -> bool:
        """
        System 36 supports both Best Gross and Best Net awards

        Best Gross: Player with lowest gross score
        Best Net: Player with lowest net score (gross - calculated handicap)

        Returns:
            True
        """
        return True

    def _calculate_system36_handicap(self, total_points: int) -> float:
        """
        Calculate System 36 handicap from total points

        Formula: System 36 Handicap = 36 - Total Points

        Args:
            total_points: Sum of all hole points (0-36)

        Returns:
            Calculated handicap for the round

        Example:
            23 points → handicap = 36 - 23 = 13
            30 points → handicap = 36 - 30 = 6
        """
        return 36 - total_points
