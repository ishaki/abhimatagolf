from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum
import re


class SexEnum(str, Enum):
    """Sex/Gender options"""
    MALE = "Male"
    FEMALE = "Female"


class EventStatusEnum(str, Enum):
    """Event participation status"""
    OK = "Ok"
    NO_SHOW = "No Show"
    DISQUALIFIED = "Disqualified"


# Common countries list for dropdown
COUNTRIES = [
    "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Argentina", "Armenia", 
    "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados",
    "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina",
    "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cambodia",
    "Cameroon", "Canada", "Cape Verde", "Central African Republic", "Chad", "Chile", "China",
    "Colombia", "Comoros", "Congo", "Costa Rica", "Croatia", "Cuba", "Cyprus", "Czech Republic",
    "Denmark", "Djibouti", "Dominica", "Dominican Republic", "East Timor", "Ecuador", "Egypt",
    "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Ethiopia", "Fiji", "Finland",
    "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala",
    "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Honduras", "Hungary", "Iceland", "India",
    "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Ivory Coast", "Jamaica", "Japan",
    "Jordan", "Kazakhstan", "Kenya", "Kiribati", "North Korea", "South Korea", "Kosovo", "Kuwait",
    "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein",
    "Lithuania", "Luxembourg", "Macedonia", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali",
    "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova",
    "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru",
    "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "Norway", "Oman",
    "Pakistan", "Palau", "Palestine", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines",
    "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis",
    "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Saudi Arabia",
    "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia",
    "Solomon Islands", "Somalia", "South Africa", "South Sudan", "Spain", "Sri Lanka", "Sudan",
    "Suriname", "Swaziland", "Sweden", "Switzerland", "Syria", "Taiwan", "Tajikistan", "Tanzania",
    "Thailand", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan",
    "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States",
    "Uruguay", "Uzbekistan", "Vanuatu", "Vatican City", "Venezuela", "Vietnam", "Yemen", "Zambia",
    "Zimbabwe"
]


class ParticipantBase(BaseModel):
    """Base participant schema"""
    name: str = Field(..., min_length=1, max_length=100, description="Participant name")
    declared_handicap: float = Field(default=0, ge=0, le=54, description="Declared golf handicap")
    division: Optional[str] = Field(None, max_length=50, description="Division category")
    division_id: Optional[int] = Field(None, description="Event Division ID")
    
    # Additional participant information (all optional)
    country: Optional[str] = Field(None, max_length=100, description="Country")
    sex: Optional[SexEnum] = Field(None, description="Sex/Gender")
    phone_no: Optional[str] = Field(None, max_length=20, description="Phone number")
    event_status: EventStatusEnum = Field(default=EventStatusEnum.OK, description="Event participation status")
    event_description: Optional[str] = Field(None, max_length=500, description="Event notes/description")
    
    @validator('phone_no')
    def validate_phone_no(cls, v):
        if v is not None:
            # Allow only numbers and + sign
            if not re.match(r'^[\d+\s()-]+$', v):
                raise ValueError('Phone number can only contain numbers, +, spaces, hyphens, and parentheses')
        return v
    
    @validator('country')
    def validate_country(cls, v):
        if v is not None and v not in COUNTRIES:
            # Allow custom countries but log a warning (for now just pass through)
            pass
        return v


class ParticipantCreate(ParticipantBase):
    """Schema for creating a participant"""
    event_id: int = Field(..., gt=0, description="Event ID")


class ParticipantUpdate(BaseModel):
    """Schema for updating a participant"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    declared_handicap: Optional[float] = Field(None, ge=0, le=54)
    division: Optional[str] = Field(None, max_length=50)
    division_id: Optional[int] = None
    
    # Additional participant information
    country: Optional[str] = Field(None, max_length=100)
    sex: Optional[SexEnum] = None
    phone_no: Optional[str] = Field(None, max_length=20)
    event_status: Optional[EventStatusEnum] = None
    event_description: Optional[str] = Field(None, max_length=500)
    
    @validator('phone_no')
    def validate_phone_no(cls, v):
        if v is not None:
            # Allow only numbers and + sign
            if not re.match(r'^[\d+\s()-]+$', v):
                raise ValueError('Phone number can only contain numbers, +, spaces, hyphens, and parentheses')
        return v


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
        use_enum_values = True  # Serialize enums as their values


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
    country: Optional[str] = None
    sex: Optional[str] = None
    phone_no: Optional[str] = None
    event_status: str = "Ok"
    event_description: Optional[str] = None

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
    
    @validator('phone_no')
    def validate_phone_no(cls, v):
        if v is not None and v.strip():
            # Allow only numbers and + sign
            if not re.match(r'^[\d+\s()-]+$', v):
                raise ValueError('Phone number can only contain numbers, +, spaces, hyphens, and parentheses')
        return v
    
    @validator('sex')
    def validate_sex(cls, v):
        if v is not None and v.strip():
            if v not in ["Male", "Female"]:
                raise ValueError('Sex must be Male or Female')
        return v
    
    @validator('event_status')
    def validate_event_status(cls, v):
        if v not in ["Ok", "No Show", "Disqualified"]:
            raise ValueError('Event status must be Ok, No Show, or Disqualified')
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
