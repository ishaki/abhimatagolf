from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime


class ParticipantBase(BaseModel):
    """Base participant schema"""
    name: str = Field(..., min_length=1, max_length=100, description="Participant name")
    declared_handicap: float = Field(default=0, ge=0, le=54, description="Declared golf handicap")
    division: Optional[str] = Field(None, max_length=50, description="Division category")
    division_id: Optional[int] = Field(None, description="Event Division ID")


class ParticipantCreate(ParticipantBase):
    """Schema for creating a participant"""
    event_id: int = Field(..., gt=0, description="Event ID")


class ParticipantUpdate(BaseModel):
    """Schema for updating a participant"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    declared_handicap: Optional[float] = Field(None, ge=0, le=54)
    division: Optional[str] = Field(None, max_length=50)
    division_id: Optional[int] = None


class ParticipantResponse(ParticipantBase):
    """Schema for participant response"""
    id: int
    event_id: int
    registered_at: datetime

    # Optional related data
    event_name: Optional[str] = None
    scorecard_count: Optional[int] = None
    total_gross_score: Optional[int] = None
    total_net_score: Optional[float] = None
    total_points: Optional[int] = None

    class Config:
        from_attributes = True


class ParticipantListResponse(BaseModel):
    """Schema for paginated participant list"""
    participants: List[ParticipantResponse]
    total: int
    page: int
    per_page: int


class ParticipantBulkCreate(BaseModel):
    """Schema for bulk participant creation"""
    event_id: int = Field(..., gt=0, description="Event ID")
    participants: List[ParticipantBase] = Field(..., min_items=1, description="List of participants")


class ParticipantImportRow(BaseModel):
    """Schema for validating imported participant data"""
    name: str
    declared_handicap: float = 0
    division: Optional[str] = None
    division_id: Optional[int] = None

    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()

    @validator('division_id')
    def validate_division_id(cls, v):
        if v is not None and (not isinstance(v, int) or v <= 0):
            raise ValueError('Division ID must be a positive integer or None')
        return v

    @validator('declared_handicap')
    def validate_handicap(cls, v):
        if v < 0 or v > 54:
            raise ValueError('Handicap must be between 0 and 54')
        return v


class ParticipantImportResult(BaseModel):
    """Schema for import results"""
    success: bool
    total_rows: int
    successful: int
    failed: int
    participants: List[ParticipantResponse]
    errors: List[dict] = Field(default_factory=list)


class ParticipantStats(BaseModel):
    """Schema for participant statistics"""
    total_participants: int
    by_division: dict
    average_handicap: float
