# Import all models to ensure they are registered with SQLModel
from .user import User, UserRole
from .course import Course, Hole, Teebox
from .event import Event, ScoringType
from .event_division import EventDivision
from .participant import Participant
from .scorecard import Scorecard, ScoreHistory
from .user_event import UserEvent, AccessLevel
from .leaderboard_cache import LeaderboardCache
from .winner_result import WinnerResult
from .winner_configuration import (
    WinnerConfiguration,
    TieBreakingMethod,
    CalculationTrigger
)

__all__ = [
    "User",
    "UserRole",
    "Course",
    "Hole",
    "Teebox",
    "Event",
    "ScoringType",
    "EventDivision",
    "Participant",
    "Scorecard",
    "ScoreHistory",
    "UserEvent",
    "AccessLevel",
    "LeaderboardCache",
    "WinnerResult",
    "WinnerConfiguration",
    "TieBreakingMethod",
    "CalculationTrigger"
]
