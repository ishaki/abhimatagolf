from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime
from enum import Enum


class AccessLevel(str, Enum):
    READ_ONLY = "read_only"
    READ_WRITE = "read_write"
    ADMIN = "admin"


class UserEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    event_id: int = Field(foreign_key="event.id")
    access_level: AccessLevel = Field(default=AccessLevel.READ_WRITE)
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    user: "User" = Relationship(back_populates="user_events")
    event: "Event" = Relationship(back_populates="user_events")
    
    class Config:
        # Ensure unique user-event combination
        unique_together = ("user_id", "event_id")
