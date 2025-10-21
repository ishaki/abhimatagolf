from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime


class Participant(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="event.id")
    name: str = Field(max_length=100)
    declared_handicap: float = Field(default=0)
    division: Optional[str] = Field(default=None, max_length=50)  # Keep for backward compatibility
    division_id: Optional[int] = Field(default=None, foreign_key="eventdivision.id")  # New field
    registered_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    event: "Event" = Relationship(back_populates="participants")
    event_division: Optional["EventDivision"] = Relationship(back_populates="participants")
    scorecards: List["Scorecard"] = Relationship(
        back_populates="participant",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
