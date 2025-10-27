from sqlmodel import SQLModel, Field, Relationship, JSON
from typing import Optional, Dict, Any
from datetime import datetime


class WinnerResult(SQLModel, table=True):
    """
    Stores calculated winner results for an event.
    Includes overall winners and division winners with tie-breaking information.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: int = Field(foreign_key="event.id", index=True)

    # Winner information
    participant_id: int = Field(foreign_key="participant.id")
    participant_name: str = Field(max_length=100)
    division: Optional[str] = Field(default=None, max_length=50)
    division_id: Optional[int] = Field(default=None, foreign_key="eventdivision.id")

    # Ranking
    overall_rank: Optional[int] = Field(default=None)  # Overall ranking in the event (optional)
    division_rank: Optional[int] = Field(default=None)  # Ranking within division

    # Scores
    gross_score: int
    net_score: Optional[int] = Field(default=None)

    # Handicap information
    declared_handicap: float  # User's input handicap (from participant form)
    course_handicap: float  # Calculated handicap based on teebox slope rating
    system36_handicap: Optional[float] = Field(default=None)  # System 36 calculated handicap (36 - total points)

    # Teebox information (for transparency and audit trail)
    teebox_name: Optional[str] = Field(default=None, max_length=50)
    teebox_course_rating: Optional[float] = Field(default=None)
    teebox_slope_rating: Optional[int] = Field(default=None)

    # Tie-breaking information
    is_tied: bool = Field(default=False)
    tied_with: Optional[Dict[str, Any]] = Field(default=None, sa_type=JSON)  # List of participant IDs tied with
    tie_break_criteria: Optional[Dict[str, Any]] = Field(default=None, sa_type=JSON)  # How tie was broken

    # Prize/Award information (optional)
    award_category: Optional[str] = Field(default=None, max_length=100)  # e.g., "Champion", "Runner-up", "Nearest to Pin"
    prize_details: Optional[str] = Field(default=None, max_length=500)

    # Metadata
    calculated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    event: "Event" = Relationship(back_populates="winner_results")
    participant: "Participant" = Relationship()
    event_division: Optional["EventDivision"] = Relationship()
