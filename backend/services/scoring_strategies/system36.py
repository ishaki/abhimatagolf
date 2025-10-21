"""
System 36 Scoring Strategy

System 36 is a unique handicapping system where points are awarded based on
performance relative to par. The system calculates a handicap from the round
being played, making it fair for players without established handicaps.

Rules:
- Points awarded per hole based on score vs par:
  * Double Eagle (-3 or better): 8 points
  * Eagle (-2): 5 points
  * Birdie (-1): 4 points
  * Par (0): 3 points
  * Bogey (+1): 2 points
  * Double Bogey (+2): 1 point
  * Triple Bogey or worse (+3+): 0 points

- Handicap calculated from points:
  * System 36 Handicap = 36 - (Total Points / Holes Played) × 18

- Net score = Gross score - System 36 Handicap
- Higher points win

Formula:
- Points per Hole = f(net_strokes, par)
- Total Points = Sum of all hole points
- System 36 HCP = 36 - (Total Points / Holes Played) × 18
- Net Score = Gross Score - System 36 HCP
- Winner = Highest total points
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
        par: int,
        handicap_strokes: int
    ) -> int:
        """
        Calculate classic System 36 points for a hole (2/1/0)

        Rules (using net vs par):
        - Par or better: 2 points
        - Bogey (+1): 1 point
        - Double bogey or worse (>= +2): 0 points
        """
        net_score = strokes - handicap_strokes
        score_to_par = net_score - par

        if score_to_par <= 0:
            return 2
        elif score_to_par == 1:
            return 1
        else:
            return 0

    def update_scorecard(
        self,
        scorecard: Scorecard,
        participant: Participant,
        hole: Hole
    ) -> Scorecard:
        """
        Update scorecard for System 36

        Calculate handicap strokes for this hole, determine points,
        and set both points and net score.

        Args:
            scorecard: Scorecard with strokes already set
            participant: Participant with declared handicap
            hole: Hole with par and difficulty index

        Returns:
            Updated scorecard with points and net_score
        """
        # Calculate handicap strokes for this specific hole
        handicap_strokes = self.calculate_handicap_strokes_for_hole(
            declared_handicap=participant.declared_handicap,
            hole_index=hole.handicap_index,
            num_holes=18
        )

        # Calculate System 36 points
        points = self.calculate_system36_points(
            strokes=scorecard.strokes,
            par=hole.par,
            handicap_strokes=handicap_strokes
        )

        # Set points (primary scoring metric)
        scorecard.points = points

        # Set net score (for display/reference)
        scorecard.net_score = int(scorecard.strokes - handicap_strokes)

        logger.debug(
            f"System 36: Participant {participant.id} (HCP {participant.declared_handicap}), "
            f"Hole {hole.number} (Par {hole.par}, Index {hole.handicap_index}), "
            f"Gross {scorecard.strokes}, Handicap Strokes {handicap_strokes}, "
            f"Net {scorecard.net_score}, Points {points}"
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
