"""
Winner Configuration Model

Stores event-level configuration for winner calculation including:
- Tie-breaking rules
- Award categories
- Winner count per division
- Calculation triggers
- Manual override permissions
"""

from sqlmodel import SQLModel, Field, Relationship, JSON
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class TieBreakingMethod(str, Enum):
    """Tie-breaking methods for winner calculation"""
    STANDARD_GOLF = "standard_golf"  # Back 9, Last 6, Last 3, Last Hole
    SCORECARD_PLAYOFF = "scorecard_playoff"  # Sudden death on scorecard
    SHARE_POSITION = "share_position"  # Multiple winners share the same rank
    LOWEST_HANDICAP = "lowest_handicap"  # Prefer player with lower handicap
    RANDOM = "random"  # Random selection (for fun events)


class CalculationTrigger(str, Enum):
    """When to automatically calculate winners"""
    MANUAL_ONLY = "manual_only"  # Only when admin clicks calculate
    ALL_SCORES_COMPLETE = "all_scores_complete"  # When all participants have 18 holes
    EVENT_END = "event_end"  # When event end date/time is reached
    SCORE_SUBMISSION = "score_submission"  # After each score submission (real-time)


class WinnerConfiguration(SQLModel, table=True):
    """
    Configuration for winner calculation per event.

    This allows each event to have custom rules for:
    - How ties are broken
    - What awards are given
    - How many winners per division
    - When winners are calculated
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="event.id", unique=True, index=True)

    # Tie-breaking configuration
    tie_breaking_method: TieBreakingMethod = Field(
        default=TieBreakingMethod.STANDARD_GOLF,
        description="Method used to break ties"
    )

    # Award categories configuration
    # Format: [{"rank": 1, "name": "Champion", "description": "Overall Winner"}, ...]
    award_categories: Dict[str, Any] = Field(
        default_factory=lambda: {
            "overall": [
                {"rank": 1, "name": "Champion", "description": "Overall Winner"},
                {"rank": 2, "name": "Runner-up", "description": "Second Place"},
                {"rank": 3, "name": "Third Place", "description": "Third Place"}
            ],
            "division": [
                {"rank": 1, "name": "Division Winner", "description": "First in Division"},
                {"rank": 2, "name": "Division Runner-up", "description": "Second in Division"}
            ]
        },
        sa_type=JSON,
        description="Award categories for overall and division winners"
    )

    # Winner count configuration
    winners_per_division: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of winners to recognize per division (1-10)"
    )

    top_overall_count: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Number of overall winners to recognize (0-10). Set to 0 to disable overall winners (division-based only)"
    )

    # Calculation trigger configuration
    calculation_trigger: CalculationTrigger = Field(
        default=CalculationTrigger.MANUAL_ONLY,
        description="When to automatically calculate winners"
    )

    # Manual override configuration
    allow_manual_override: bool = Field(
        default=True,
        description="Allow event admins to manually edit winner results"
    )

    # Additional settings
    include_best_gross: bool = Field(
        default=False,
        description="Include 'Best Gross Score' award"
    )

    include_best_net: bool = Field(
        default=False,
        description="Include 'Best Net Score' award"
    )

    exclude_incomplete_rounds: bool = Field(
        default=True,
        description="Exclude participants who haven't completed all 18 holes"
    )

    minimum_holes_for_ranking: int = Field(
        default=18,
        ge=9,
        le=18,
        description="Minimum holes required to be eligible for ranking"
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: int = Field(foreign_key="user.id")

    # Relationships
    event: "Event" = Relationship(back_populates="winner_config")
    creator: "User" = Relationship()
