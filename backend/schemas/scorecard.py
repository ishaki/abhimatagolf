from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
from core.validation import SecurityValidators


class HoleScoreInput(BaseModel):
    """Input for a single hole score"""
    hole_number: int = Field(ge=1, le=18, description="Hole number (1-18)")
    strokes: int = Field(ge=1, le=15, description="Number of strokes (1-15)")
    
    @validator('hole_number')
    def validate_hole_number(cls, v):
        """Validate hole number"""
        return SecurityValidators.validate_hole_number(cls, v)
    
    @validator('strokes')
    def validate_strokes(cls, v):
        """Validate stroke count"""
        return SecurityValidators.validate_strokes(cls, v)


class ScorecardSubmit(BaseModel):
    """Submit scorecard for a participant"""
    participant_id: int = Field(..., gt=0, description="Participant ID")
    scores: List[HoleScoreInput] = Field(min_items=1, max_items=18, description="List of hole scores")
    
    @validator('participant_id')
    def validate_participant_id(cls, v):
        """Validate participant ID"""
        if v <= 0:
            raise ValueError("Participant ID must be positive")
        return v


class HoleScoreResponse(BaseModel):
    """Response for a single hole score"""
    id: int
    hole_number: int
    hole_par: int
    hole_distance: int
    handicap_index: int
    strokes: int
    score_to_par: int  # e.g., +1, -1, 0 (E)
    color_code: str  # "birdie", "par", "bogey", "double_bogey"
    system36_points: Optional[int] = Field(None, description="System 36 points for this hole")

    class Config:
        from_attributes = True


class ScorecardResponse(BaseModel):
    """Complete scorecard response"""
    participant_id: int
    participant_name: str
    event_id: int
    event_name: str
    handicap: float
    country: Optional[str] = Field(default=None, description="Participant's country")

    # Front 9
    front_nine: List[HoleScoreResponse]
    out_total: int
    out_to_par: int

    # Back 9
    back_nine: List[HoleScoreResponse]
    in_total: int
    in_to_par: int

    # Totals
    gross_score: int
    net_score: int
    score_to_par: int
    course_par: int
    holes_completed: int

    # System 36 totals (optional, only for system_36 events)
    system36_points: Optional[int] = Field(default=None, description="Total System 36 points for the round")

    # Metadata
    last_updated: Optional[datetime]
    recorded_by: Optional[str]

    class Config:
        from_attributes = True


class ScorecardListResponse(BaseModel):
    """List of scorecards"""
    scorecards: List[ScorecardResponse]
    total: int


class ScoreUpdate(BaseModel):
    """Update a single hole score"""
    strokes: int = Field(ge=1, le=15)
    reason: Optional[str] = None


class ScoreHistoryResponse(BaseModel):
    """Score history entry"""
    id: int
    scorecard_id: int
    old_strokes: int
    new_strokes: int
    modified_by: str
    modified_at: datetime
    reason: Optional[str]

    class Config:
        from_attributes = True
