from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime


class EventDivision(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="event.id")
    name: str = Field(max_length=100, description="Division name (e.g., Championship, Senior, Ladies)")
    description: Optional[str] = Field(default=None, max_length=500, description="Optional division description")
    handicap_min: Optional[float] = Field(default=None, description="Minimum handicap for this division")
    handicap_max: Optional[float] = Field(default=None, description="Maximum handicap for this division")
    max_participants: Optional[int] = Field(default=None, description="Maximum number of participants allowed")
    is_active: bool = Field(default=True, description="Whether this division is active")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    event: "Event" = Relationship(back_populates="divisions")
    participants: List["Participant"] = Relationship(back_populates="event_division")
