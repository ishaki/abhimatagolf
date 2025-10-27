from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from schemas.course import TeeboxResponse
from models.event_division import DivisionType


class EventDivisionBase(BaseModel):
    name: str = Field(max_length=100, description="Division name (e.g., Championship, Senior, Ladies)")
    description: Optional[str] = Field(default=None, max_length=500, description="Optional division description")
    division_type: Optional[DivisionType] = Field(default=None, description="Type of division (Men, Women, Senior, VIP, Mixed)")
    handicap_min: Optional[float] = Field(default=None, description="Minimum handicap for this division")
    handicap_max: Optional[float] = Field(default=None, description="Maximum handicap for this division")
    use_course_handicap_for_assignment: Optional[bool] = Field(default=None, description="Use course handicap instead of declared handicap for division assignment (System 36 Men divisions only). Default is auto-determined based on event scoring type.")
    max_participants: Optional[int] = Field(default=None, description="Maximum number of participants allowed")
    teebox_id: Optional[int] = Field(default=None, description="Teebox assigned to this division")
    is_active: bool = Field(default=True, description="Whether this division is active")


class EventDivisionCreate(EventDivisionBase):
    event_id: int = Field(description="ID of the event this division belongs to")


class EventDivisionUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    division_type: Optional[DivisionType] = Field(default=None)
    handicap_min: Optional[float] = Field(default=None)
    handicap_max: Optional[float] = Field(default=None)
    use_course_handicap_for_assignment: Optional[bool] = Field(default=None)
    max_participants: Optional[int] = Field(default=None)
    teebox_id: Optional[int] = Field(default=None)
    is_active: Optional[bool] = Field(default=None)


class EventDivisionResponse(EventDivisionBase):
    id: int
    event_id: int
    created_at: datetime
    updated_at: datetime
    participant_count: Optional[int] = Field(default=None, description="Number of participants in this division")
    teebox: Optional[TeeboxResponse] = Field(default=None, description="Teebox information for this division")

    class Config:
        from_attributes = True


class EventDivisionBulkCreate(BaseModel):
    event_id: int
    divisions: list[EventDivisionBase] = Field(description="List of divisions to create")
