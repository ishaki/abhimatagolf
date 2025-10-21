"""
Base scoring strategy interface

This module defines the abstract base class for all scoring strategies.
Each scoring system (Stroke, Net Stroke, System 36, Stableford) implements
this interface to provide consistent behavior across different scoring types.

The Strategy Pattern allows us to:
1. Calculate scores once during entry (not on every display)
2. Store calculated values in database
3. Easily add new scoring systems without modifying existing code
4. Maintain consistent interface across all scoring types
"""

from abc import ABC, abstractmethod
from typing import Tuple
from models.scorecard import Scorecard
from models.participant import Participant
from models.course import Hole
from schemas.leaderboard import LeaderboardEntry


class ScoringStrategy(ABC):
    """
    Abstract base class for all scoring strategies

    Each concrete strategy must implement:
    - update_scorecard(): Calculate and store scoring-specific values
    - get_sort_key(): Define how leaderboard entries are ranked
    - validate_score(): Validate score is appropriate for this scoring type
    """

    @abstractmethod
    def update_scorecard(
        self,
        scorecard: Scorecard,
        participant: Participant,
        hole: Hole
    ) -> Scorecard:
        """
        Calculate and update scorecard with scoring-specific values

        This method is called after strokes are saved. It should:
        1. Calculate derived values (points, net_score, etc.)
        2. Update scorecard fields
        3. Return updated scorecard

        Args:
            scorecard: The scorecard to update (already has strokes set)
            participant: The participant playing
            hole: The hole being scored

        Returns:
            Updated scorecard with calculated values

        Example:
            For Net Stroke Play:
            - Calculate handicap strokes for this hole
            - Set net_score = strokes - handicap_strokes
            - Set points = 0 (not used)
        """
        pass

    @abstractmethod
    def get_sort_key(self, entry: LeaderboardEntry) -> Tuple:
        """
        Return sort key for leaderboard ranking

        Defines how entries are compared and ranked. Python sorts tuples
        element by element, so first element is primary sort, second is
        tiebreaker, etc.

        Args:
            entry: Leaderboard entry to generate sort key for

        Returns:
            Tuple of comparable values for sorting

        Examples:
            Stroke Play (lowest gross wins):
                return (entry.gross_score, entry.handicap)

            System 36 (highest points wins):
                return (-entry.system36_points, entry.handicap)
                # Negative to sort descending
        """
        pass

    def validate_score(
        self,
        strokes: int,
        par: int,
        handicap: float
    ) -> Tuple[bool, str]:
        """
        Validate that score is appropriate for this scoring type

        Default implementation allows any valid stroke count.
        Override for scoring-specific validation.

        Args:
            strokes: Number of strokes taken
            par: Par for the hole
            handicap: Player's declared handicap

        Returns:
            Tuple of (is_valid, error_message)

        Example:
            return (True, "") if valid
            return (False, "Score too high") if invalid
        """
        # Basic validation: strokes must be positive and reasonable
        if strokes < 1:
            return (False, "Strokes must be at least 1")

        if strokes > par + 10:
            return (False, f"Score of {strokes} seems unusually high for par {par}")

        return (True, "")

    def calculate_handicap_strokes_for_hole(
        self,
        declared_handicap: float,
        hole_index: int,
        num_holes: int = 18
    ) -> int:
        """
        Calculate handicap strokes received on a specific hole

        Standard USGA handicap allocation:
        - Distribute handicap strokes across holes based on difficulty (index)
        - Harder holes (lower index) get strokes first
        - For handicap > 18, some holes get multiple strokes

        Args:
            declared_handicap: Player's declared handicap
            hole_index: Hole difficulty index (1-18, 1 being hardest)
            num_holes: Number of holes in round (default 18)

        Returns:
            Number of handicap strokes for this hole

        Example:
            Handicap 9, Hole Index 5:
            - First 9 hardest holes (index 1-9) get 1 stroke
            - This hole (index 5) gets 1 stroke

            Handicap 22, Hole Index 3:
            - All 18 holes get 1 stroke (18 total)
            - First 4 hardest holes (index 1-4) get additional stroke
            - This hole (index 3) gets 2 strokes total
        """
        if declared_handicap <= 0:
            return 0

        # Full strokes (every hole gets this many)
        base_strokes = int(declared_handicap // num_holes)

        # Remaining strokes distributed to hardest holes
        remaining = int(declared_handicap % num_holes)

        # If this hole's index is within remaining count, it gets extra stroke
        if hole_index <= remaining:
            return base_strokes + 1
        else:
            return base_strokes
