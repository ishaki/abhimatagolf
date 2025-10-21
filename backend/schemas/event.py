from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime, date
from models.event import ScoringType


class EventCreate(BaseModel):
    name: str
    description: Optional[str] = None
    event_date: date
    course_id: int
    scoring_type: ScoringType
    is_active: bool = True


class EventUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    event_date: Optional[date] = None
    course_id: Optional[int] = None
    scoring_type: Optional[ScoringType] = None
    divisions_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class EventResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    event_date: date
    course_id: int
    created_by: int
    scoring_type: ScoringType
    divisions_config: Optional[Dict[str, Any]] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    # Related data
    course_name: Optional[str] = None
    creator_name: Optional[str] = None
    participant_count: Optional[int] = None


class EventListResponse(BaseModel):
    events: List[EventResponse]
    total: int
    page: int
    per_page: int


class EventStats(BaseModel):
    total_events: int
    active_events: int
    upcoming_events: int
    completed_events: int
