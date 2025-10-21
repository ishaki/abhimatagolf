from sqlmodel import SQLModel, Field, Relationship, JSON
from typing import Optional, Dict, Any
from datetime import datetime


class LeaderboardCache(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="event.id")
    leaderboard_data: Dict[str, Any] = Field(sa_type=JSON)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    event: "Event" = Relationship(back_populates="leaderboard_cache")
