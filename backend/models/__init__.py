# Import all models to ensure they are registered with SQLModel
from .user import User, UserRole
from .course import Course, Hole
from .event import Event, ScoringType
from .event_division import EventDivision
from .participant import Participant
from .scorecard import Scorecard, ScoreHistory
from .user_event import UserEvent, AccessLevel
from .leaderboard_cache import LeaderboardCache

__all__ = [
    "User",
    "UserRole",
    "Course",
    "Hole",
    "Event",
    "ScoringType",
    "EventDivision",
    "Participant",
    "Scorecard",
    "ScoreHistory",
    "UserEvent",
    "AccessLevel",
    "LeaderboardCache"
]
