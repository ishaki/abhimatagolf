from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ScoringType(str, Enum):
    """Scoring types for leaderboard calculation"""
    STROKE = "stroke"
    NET_STROKE = "net_stroke"
    SYSTEM_36 = "system_36"
    STABLEFORD = "stableford"


class LeaderboardEntry(BaseModel):
    """Individual leaderboard entry"""
    rank: int = Field(..., description="Player rank (1-based)")
    participant_id: int = Field(..., description="Participant ID")
    participant_name: str = Field(..., description="Participant name")
    handicap: float = Field(..., description="Player handicap")
    division: Optional[str] = Field(None, description="Division name")
    division_id: Optional[int] = Field(None, description="Division ID")
    
    # Scoring data
    gross_score: int = Field(..., description="Total gross score")
    net_score: int = Field(..., description="Total net score")
    score_to_par: float = Field(..., description="Score relative to par")
    holes_completed: int = Field(..., description="Number of holes completed")
    
    # System 36 specific fields
    system36_points: Optional[int] = Field(None, description="Total System 36 points")
    system36_handicap: Optional[float] = Field(None, description="System 36 handicap")
    
    # Additional data
    thru: str = Field(..., description="Holes completed (e.g., 'F', '18')")
    last_updated: Optional[datetime] = Field(None, description="Last score update time")
    
    class Config:
        from_attributes = True


class LeaderboardResponse(BaseModel):
    """Complete leaderboard response"""
    event_id: int = Field(..., description="Event ID")
    event_name: str = Field(..., description="Event name")
    course_name: str = Field(..., description="Course name")
    scoring_type: ScoringType = Field(..., description="Scoring type")
    course_par: int = Field(..., description="Total course par")
    
    # Leaderboard data
    entries: List[LeaderboardEntry] = Field(..., description="Leaderboard entries")
    total_participants: int = Field(..., description="Total participants")
    participants_with_scores: int = Field(..., description="Participants with scores")
    
    # Metadata
    last_updated: datetime = Field(..., description="Last leaderboard update")
    cache_timestamp: Optional[datetime] = Field(None, description="Cache timestamp")
    
    class Config:
        from_attributes = True


class PublicLeaderboardResponse(BaseModel):
    """Public leaderboard response (no auth required)"""
    event_id: int = Field(..., description="Event ID")
    event_name: str = Field(..., description="Event name")
    course_name: str = Field(..., description="Course name")
    scoring_type: ScoringType = Field(..., description="Scoring type")
    
    # Simplified leaderboard data
    entries: List[LeaderboardEntry] = Field(..., description="Leaderboard entries")
    total_participants: int = Field(..., description="Total participants")
    
    # Metadata
    last_updated: datetime = Field(..., description="Last leaderboard update")
    
    class Config:
        from_attributes = True


class LeaderboardFilter(BaseModel):
    """Leaderboard filtering options"""
    division_id: Optional[int] = Field(None, description="Filter by division ID")
    division_name: Optional[str] = Field(None, description="Filter by division name")
    min_holes: Optional[int] = Field(None, description="Minimum holes completed")
    max_rank: Optional[int] = Field(None, description="Maximum rank to show")


class LeaderboardStats(BaseModel):
    """Leaderboard statistics"""
    total_participants: int
    participants_with_scores: int
    average_score: float
    low_score: int
    high_score: int
    cut_line: Optional[int] = Field(None, description="Cut line score")
    leader_margin: Optional[int] = Field(None, description="Leader's margin")
    
    class Config:
        from_attributes = True
