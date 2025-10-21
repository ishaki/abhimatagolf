"""
Stroke Play Scoring Strategy

Stroke Play (also called Medal Play) is the most basic golf scoring format.
The player with the lowest total number of strokes wins.

Rules:
- Count total strokes taken for all holes
- No handicap adjustment
- Lowest score wins
- Ties remain ties (or decided by playoff)

Formula:
- Total Score = Sum of all strokes
- Winner = Lowest total score
"""

from typing import Tuple
from services.scoring_strategies.base import ScoringStrategy
from models.scorecard import Scorecard
from models.participant import Participant
from models.course import Hole
from schemas.leaderboard import LeaderboardEntry
from core.app_logging import logger


class StrokeScoringStrategy(ScoringStrategy):
    """
    Stroke Play scoring strategy implementation

    This is the simplest scoring format - just count strokes.
    No handicap is applied, no points system.
    """

    def update_scorecard(
        self,
        scorecard: Scorecard,
        participant: Participant,
        hole: Hole
    ) -> Scorecard:
        """
        Update scorecard for Stroke Play

        For Stroke Play:
        - net_score = strokes (no handicap applied)
        - points = 0 (not used in stroke play)

        Args:
            scorecard: Scorecard with strokes already set
            participant: Participant (not used in stroke play)
            hole: Hole being scored (not used in stroke play)

        Returns:
            Updated scorecard
        """
        # In stroke play, net score equals gross score (no handicap)
        scorecard.net_score = float(scorecard.strokes)

        # Points not used in stroke play
        scorecard.points = 0

        logger.debug(
            f"Stroke Play: Participant {participant.id}, "
            f"Hole {hole.number}, Strokes {scorecard.strokes}, "
            f"Net {scorecard.net_score}"
        )

        return scorecard

    def get_sort_key(self, entry: LeaderboardEntry) -> Tuple:
        """
        Sort key for Stroke Play leaderboard

        Sort by:
        1. Lowest gross score (primary)
        2. Lowest handicap (tiebreaker)

        Args:
            entry: Leaderboard entry

        Returns:
            Tuple for sorting (lower is better)

        Example:
            Player A: 72 strokes, 9 handicap → (72, 9)
            Player B: 72 strokes, 18 handicap → (72, 18)
            Player A ranks higher (better) due to lower handicap
        """
        return (entry.gross_score, entry.handicap)

    def validate_score(
        self,
        strokes: int,
        par: int,
        handicap: float
    ) -> Tuple[bool, str]:
        """
        Validate score for Stroke Play

        Uses default validation from base class.
        Stroke Play accepts any reasonable stroke count.

        Args:
            strokes: Number of strokes
            par: Par for the hole
            handicap: Player's handicap (not used in validation)

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Use base class validation
        return super().validate_score(strokes, par, handicap)
