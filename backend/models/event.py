from sqlmodel import SQLModel, Field, Relationship, JSON
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum


class ScoringType(str, Enum):
    STROKE = "stroke"
    NET_STROKE = "net_stroke"
    SYSTEM_36 = "system_36"
    STABLEFORD = "stableford"


class Event(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    event_date: date
    course_id: int = Field(foreign_key="course.id")
    created_by: int = Field(foreign_key="user.id")
    scoring_type: ScoringType
    divisions_config: Optional[Dict[str, Any]] = Field(default=None, sa_type=JSON)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    course: "Course" = Relationship(back_populates="events")
    creator: "User" = Relationship(back_populates="created_events")
    participants: List["Participant"] = Relationship(back_populates="event")
    divisions: List["EventDivision"] = Relationship(back_populates="event")
    user_events: List["UserEvent"] = Relationship(back_populates="event")
    scorecards: List["Scorecard"] = Relationship(back_populates="event")
    leaderboard_cache: List["LeaderboardCache"] = Relationship(back_populates="event")
    winner_results: List["WinnerResult"] = Relationship(back_populates="event")
