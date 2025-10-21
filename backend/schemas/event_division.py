from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class EventDivisionBase(BaseModel):
    name: str = Field(max_length=100, description="Division name (e.g., Championship, Senior, Ladies)")
    description: Optional[str] = Field(default=None, max_length=500, description="Optional division description")
    handicap_min: Optional[float] = Field(default=None, description="Minimum handicap for this division")
    handicap_max: Optional[float] = Field(default=None, description="Maximum handicap for this division")
    max_participants: Optional[int] = Field(default=None, description="Maximum number of participants allowed")
    is_active: bool = Field(default=True, description="Whether this division is active")


class EventDivisionCreate(EventDivisionBase):
    event_id: int = Field(description="ID of the event this division belongs to")


class EventDivisionUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    handicap_min: Optional[float] = Field(default=None)
    handicap_max: Optional[float] = Field(default=None)
    max_participants: Optional[int] = Field(default=None)
    is_active: Optional[bool] = Field(default=None)


class EventDivisionResponse(EventDivisionBase):
    id: int
    event_id: int
    created_at: datetime
    updated_at: datetime
    participant_count: Optional[int] = Field(default=None, description="Number of participants in this division")

    class Config:
        from_attributes = True


class EventDivisionBulkCreate(BaseModel):
    event_id: int
    divisions: list[EventDivisionBase] = Field(description="List of divisions to create")
