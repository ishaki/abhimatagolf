from pydantic import BaseModel, validator, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, date
from models.event import ScoringType
from core.validation import SecurityValidators


class EventCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200, description="Event name")
    description: Optional[str] = Field(None, max_length=1000, description="Event description")
    event_date: date = Field(..., description="Event date")
    course_id: int = Field(..., gt=0, description="Course ID")
    scoring_type: ScoringType = Field(..., description="Scoring type")
    is_active: bool = Field(default=True, description="Whether event is active")
    
    @validator('name')
    def validate_name(cls, v):
        """Validate and sanitize event name"""
        return SecurityValidators.validate_text_content(cls, v, max_length=200)
    
    @validator('description')
    def validate_description(cls, v):
        """Validate and sanitize event description"""
        if v is not None:
            return SecurityValidators.validate_text_content(cls, v, max_length=1000)
        return v
    
    @validator('event_date')
    def validate_event_date(cls, v):
        """Validate event date is not in the past"""
        if v < date.today():
            raise ValueError("Event date cannot be in the past")
        return v


class EventUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200, description="Event name")
    description: Optional[str] = Field(None, max_length=1000, description="Event description")
    event_date: Optional[date] = Field(None, description="Event date")
    course_id: Optional[int] = Field(None, gt=0, description="Course ID")
    scoring_type: Optional[ScoringType] = Field(None, description="Scoring type")
    divisions_config: Optional[Dict[str, Any]] = Field(None, description="Divisions configuration")
    is_active: Optional[bool] = Field(None, description="Whether event is active")
    
    @validator('name')
    def validate_name(cls, v):
        """Validate and sanitize event name"""
        if v is not None:
            return SecurityValidators.validate_text_content(cls, v, max_length=200)
        return v
    
    @validator('description')
    def validate_description(cls, v):
        """Validate and sanitize event description"""
        if v is not None:
            return SecurityValidators.validate_text_content(cls, v, max_length=1000)
        return v
    
    @validator('event_date')
    def validate_event_date(cls, v):
        """Validate event date is not in the past"""
        if v is not None and v < date.today():
            raise ValueError("Event date cannot be in the past")
        return v


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
