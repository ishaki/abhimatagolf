"""
Net Stroke Play Scoring Strategy

Net Stroke Play is similar to Stroke Play but applies handicap adjustments.
The player with the lowest net score (gross - handicap) wins.

Rules:
- Handicap strokes distributed across holes by difficulty
- Hardest holes (lowest index) receive strokes first
- Net score = Gross strokes - Handicap strokes
- Lowest net score wins

Formula:
- Handicap Strokes per Hole = f(declared_handicap, hole_index)
- Net Score per Hole = Gross Strokes - Handicap Strokes
- Total Net Score = Sum of all net scores
- Winner = Lowest total net score
"""

from typing import Tuple
from services.scoring_strategies.base import ScoringStrategy
from models.scorecard import Scorecard
from models.participant import Participant
from models.course import Hole
from schemas.leaderboard import LeaderboardEntry
from core.app_logging import logger


class NetStrokeScoringStrategy(ScoringStrategy):
    """
    Net Stroke Play scoring strategy implementation

    Applies handicap adjustments to each hole based on difficulty.
    Net score is calculated per hole, then summed for total.
    """

    def update_scorecard(
        self,
        scorecard: Scorecard,
        participant: Participant,
        hole: Hole
    ) -> Scorecard:
        """
        Update scorecard for Net Stroke Play

        Calculate handicap strokes for this hole and set net score.

        Args:
            scorecard: Scorecard with strokes already set
            participant: Participant with declared handicap
            hole: Hole with difficulty index

        Returns:
            Updated scorecard with net_score calculated
        """
        # Calculate handicap strokes for this specific hole
        handicap_strokes = self.calculate_handicap_strokes_for_hole(
            declared_handicap=participant.declared_handicap,
            hole_index=hole.stroke_index,
            num_holes=18
        )

        # Net score = Gross strokes - Handicap strokes received
        scorecard.net_score = float(scorecard.strokes - handicap_strokes)

        # Points not used in net stroke play
        scorecard.points = 0

        logger.debug(
            f"Net Stroke Play: Participant {participant.id} (HCP {participant.declared_handicap}), "
            f"Hole {hole.number} (Index {hole.stroke_index}), "
            f"Gross {scorecard.strokes}, Handicap Strokes {handicap_strokes}, "
            f"Net {scorecard.net_score}"
        )

        return scorecard

    def get_sort_key(self, entry: LeaderboardEntry) -> Tuple:
        """
        Sort key for Net Stroke Play leaderboard

        Sort by:
        1. Lowest net score (primary)
        2. Lowest handicap (tiebreaker)

        In net stroke play, lower handicap players have advantage in ties
        as they shot relatively better golf.

        Args:
            entry: Leaderboard entry

        Returns:
            Tuple for sorting (lower is better)

        Example:
            Player A: Net 72, HCP 9 → (72, 9)
            Player B: Net 72, HCP 18 → (72, 18)
            Player A ranks higher due to lower handicap
        """
        return (entry.net_score, entry.handicap)

    def validate_score(
        self,
        strokes: int,
        par: int,
        handicap: float
    ) -> Tuple[bool, str]:
        """
        Validate score for Net Stroke Play

        Args:
            strokes: Number of strokes
            par: Par for the hole
            handicap: Player's declared handicap

        Returns:
            Tuple of (is_valid, error_message)
        """
        # First do basic validation
        is_valid, error_msg = super().validate_score(strokes, par, handicap)
        if not is_valid:
            return (is_valid, error_msg)

        # Additional validation: check handicap range
        if handicap < 0:
            return (False, "Handicap cannot be negative")

        if handicap > 54:
            return (False, "Handicap cannot exceed 54")

        return (True, "")
