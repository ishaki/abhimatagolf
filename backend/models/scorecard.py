from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime


class Scorecard(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    participant_id: int = Field(foreign_key="participant.id")
    hole_id: int = Field(foreign_key="hole.id")
    event_id: int = Field(foreign_key="event.id")  # Added for easier querying
    strokes: int = Field(ge=1, le=15)  # Validation: 1-15 strokes
    points: int = Field(default=0)  # For Stableford/System 36
    net_score: float = Field(default=0)
    recorded_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)  # Track updates
    recorded_by: int = Field(foreign_key="user.id")

    # Relationships
    participant: "Participant" = Relationship(back_populates="scorecards")
    hole: "Hole" = Relationship(back_populates="scorecards")
    event: "Event" = Relationship(back_populates="scorecards")
    recorder: "User" = Relationship(back_populates="recorded_scores")

    class Config:
        # Ensure unique score per participant per hole
        unique_together = ("participant_id", "hole_id")


class ScoreHistory(SQLModel, table=True):
    """Track score changes for audit trail"""
    id: Optional[int] = Field(default=None, primary_key=True)
    scorecard_id: int = Field(foreign_key="scorecard.id")
    old_strokes: int
    new_strokes: int
    modified_by: int = Field(foreign_key="user.id")
    modified_at: datetime = Field(default_factory=datetime.utcnow)
    reason: Optional[str] = None
