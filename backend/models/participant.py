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
    
    # Additional participant information (all optional)
    country: Optional[str] = Field(default=None, max_length=100)
    sex: Optional[str] = Field(default=None, max_length=10)  # Male/Female
    phone_no: Optional[str] = Field(default=None, max_length=20)
    event_status: str = Field(default="Ok", max_length=50)  # Ok, No Show, Disqualified
    event_description: Optional[str] = Field(default=None, max_length=500)
    
    # Relationships
    event: "Event" = Relationship(back_populates="participants")
    event_division: Optional["EventDivision"] = Relationship(back_populates="participants")
    scorecards: List["Scorecard"] = Relationship(
        back_populates="participant",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    @property
    def teebox(self):
        """Get the teebox assigned to this participant through their division"""
        if self.event_division and self.event_division.teebox:
            return self.event_division.teebox
        return None

    @property
    def course_handicap(self) -> float:
        """Calculate course handicap based on teebox slope rating

        Formula: (Handicap Index × Slope Rating) / 113
        """
        if self.teebox and self.teebox.slope_rating:
            return (self.declared_handicap * self.teebox.slope_rating) / 113.0
        # Fallback to declared handicap if no teebox assigned
        return self.declared_handicap
