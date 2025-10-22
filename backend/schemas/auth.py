from pydantic import BaseModel, validator, Field
from typing import Optional
from datetime import datetime
from models.user import UserRole
from core.validation import SecurityValidators


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class TokenData(BaseModel):
    email: Optional[str] = None


class UserLogin(BaseModel):
    email: str = Field(..., max_length=254, description="User's email address")
    password: str = Field(..., min_length=1, max_length=128, description="User's password")
    
    @validator('email')
    def validate_email(cls, v):
        """Validate and sanitize email format"""
        return SecurityValidators.validate_email(cls, v)
