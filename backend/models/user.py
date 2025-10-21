from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    EVENT_ADMIN = "event_admin"
    EVENT_USER = "event_user"


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    full_name: str = Field(max_length=100)
    email: str = Field(max_length=255, unique=True, index=True)
    hashed_password: str = Field(max_length=255)
    role: UserRole = Field(default=UserRole.EVENT_USER)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    created_events: List["Event"] = Relationship(back_populates="creator")
    user_events: List["UserEvent"] = Relationship(back_populates="user")
    recorded_scores: List["Scorecard"] = Relationship(back_populates="recorder")
