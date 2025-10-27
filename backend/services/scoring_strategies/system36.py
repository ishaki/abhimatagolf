"""
System 36 Scoring Strategy

System 36 is a same-day handicapping system for golfers without official handicaps.
Points are awarded based on GROSS score performance, and a handicap is calculated
from the round being played.

Official Rules (GROSS Scoring):
- Points awarded per hole based on GROSS score vs par:
  * Par or better (≤0): 2 points
  * Bogey (+1): 1 point
  * Double Bogey or worse (≥+2): 0 points

- System 36 Handicap (calculated after full 18 holes):
  * System 36 Handicap = 36 - Total Points
  * Only calculated for complete 18-hole rounds
  * Example: Player scores 23 total points
    - System 36 Handicap = 36 - 23 = 13
    - If gross score is 90, net score = 90 - 13 = 77

- Net score = Gross score - System 36 Handicap (applied after full round)
- Higher total points win

Formula:
- Points per Hole = f(gross_strokes, par)
  * Par or better (gross ≤ par): 2 points
  * Bogey (gross = par + 1): 1 point
  * Double bogey or worse (gross ≥ par + 2): 0 points
- Total Points = Sum of all hole points
- System 36 Handicap = 36 - Total Points (18 holes only)
- Net Score = Gross Score - System 36 Handicap
- Winner = Highest total points

Example Round:
- 7 pars × 2 = 14 points
- 9 bogeys × 1 = 9 points
- 2 doubles × 0 = 0 points
- Total = 23 points, Handicap = 36 - 23 = 13
"""

from typing import Tuple
from services.scoring_strategies.base import ScoringStrategy
from models.scorecard import Scorecard
from models.participant import Participant
from models.course import Hole
from schemas.leaderboard import LeaderboardEntry
from core.app_logging import logger


class System36ScoringStrategy(ScoringStrategy):
    """
    System 36 scoring strategy implementation

    Awards points based on performance and calculates handicap from points.
    """

    def calculate_system36_points(
        self,
        strokes: int,
        par: int
    ) -> int:
        """
        Calculate official System 36 points for a hole (2/1/0)

        Official Rules (using GROSS score vs par):
        - Par or better (gross ≤ par): 2 points
        - Bogey (gross = par + 1): 1 point
        - Double bogey or worse (gross ≥ par + 2): 0 points

        Args:
            strokes: Gross strokes on the hole
            par: Par for the hole

        Returns:
            Points earned (0, 1, or 2)

        Example:
            Par 4, Gross 5 (bogey) → 1 point
            Par 4, Gross 4 (par) → 2 points
            Par 4, Gross 6 (double) → 0 points
        """
        score_to_par = strokes - par

        if score_to_par <= 0:  # Par or better
            return 2
        elif score_to_par == 1:  # Bogey
            return 1
        else:  # Double bogey or worse
            return 0

    def update_scorecard(
        self,
        scorecard: Scorecard,
        participant: Participant,
        hole: Hole
    ) -> Scorecard:
        """
        Update scorecard for System 36

        Calculate points based on GROSS score vs par.
        Note: System 36 handicap is calculated after the full round,
        not applied per hole.

        Args:
            scorecard: Scorecard with strokes already set
            participant: Participant (not used for System 36 per-hole calculation)
            hole: Hole with par

        Returns:
            Updated scorecard with points
        """
        # Calculate System 36 points based on GROSS score
        points = self.calculate_system36_points(
            strokes=scorecard.strokes,
            par=hole.par
        )

        # Set points (primary scoring metric)
        scorecard.points = points

        # Net score is not applicable per hole in System 36
        # It's calculated after the full round: Gross - (36 - Total Points)
        # Set to gross strokes as placeholder to satisfy NOT NULL constraint
        scorecard.net_score = scorecard.strokes

        logger.debug(
            f"System 36: Participant {participant.id}, "
            f"Hole {hole.number} (Par {hole.par}), "
            f"Gross {scorecard.strokes}, Points {points}"
        )

        return scorecard

    def get_sort_key(self, entry: LeaderboardEntry) -> Tuple:
        """
        Sort key for System 36 leaderboard

        Sort by:
        1. Highest points (primary) - use negative for descending sort
        2. Lowest gross score (tiebreaker)
        3. Lowest handicap (second tiebreaker)

        Args:
            entry: Leaderboard entry

        Returns:
            Tuple for sorting

        Example:
            Player A: 45 points, 82 gross → (-45, 82, ...)
            Player B: 45 points, 85 gross → (-45, 85, ...)
            Player A ranks higher due to lower gross score
        """
        return (
            -entry.system36_points,  # Negative to sort descending (higher points first)
            entry.gross_score,  # Lower gross as tiebreaker
            entry.handicap  # Lower handicap as second tiebreaker
        )

    def validate_score(
        self,
        strokes: int,
        par: int,
        handicap: float
    ) -> Tuple[bool, str]:
        """
        Validate score for System 36

        Args:
            strokes: Number of strokes
            par: Par for the hole
            handicap: Player's declared handicap

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Use base class validation
        is_valid, error_msg = super().validate_score(strokes, par, handicap)
        if not is_valid:
            return (is_valid, error_msg)

        # Additional validation for System 36
        if handicap > 54:
            return (False, "Handicap cannot exceed 54 for System 36")

        return (True, "")

    def calculate_system36_handicap(
        self,
        total_points: int,
        holes_played: int
    ) -> float:
        """
        Calculate System 36 handicap for a full 18-hole round only.

        Classic rule (per user spec):
        - Full round: handicap = 36 - total_points
        - Partial round: do not compute (return 0.0)
        """
        if holes_played != 18:
            return 0.0

        handicap = 36 - total_points
        return float(handicap)
