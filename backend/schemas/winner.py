from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class WinnerResultResponse(BaseModel):
    """Response schema for winner results"""
    id: int
    event_id: int
    participant_id: int
    participant_name: str
    division: Optional[str] = None
    division_id: Optional[int] = None
    overall_rank: int
    division_rank: Optional[int] = None
    gross_score: int
    net_score: Optional[int] = None
    handicap: float
    is_tied: bool
    tied_with: Optional[Dict[str, Any]] = None
    tie_break_criteria: Optional[Dict[str, Any]] = None
    award_category: Optional[str] = None
    prize_details: Optional[str] = None
    calculated_at: datetime

    class Config:
        from_attributes = True


class CalculateWinnersRequest(BaseModel):
    """Request to calculate winners for an event"""
    event_id: int


class WinnersListResponse(BaseModel):
    """Response with list of winners"""
    event_id: int
    event_name: str
    total_winners: int
    winners: list[WinnerResultResponse]
