from pydantic import BaseModel, validator, Field
from typing import Optional, List
from datetime import datetime
from models.user import UserRole
from core.validation import SecurityValidators, ValidationError


class UserCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100, description="User's full name")
    email: str = Field(..., max_length=254, description="User's email address")
    password: str = Field(..., min_length=8, max_length=128, description="User's password")
    role: UserRole = Field(default=UserRole.EVENT_USER, description="User's role")
    is_active: bool = Field(default=True, description="Whether user account is active")
    
    @validator('full_name')
    def validate_full_name(cls, v):
        """Validate and sanitize full name"""
        return SecurityValidators.validate_name(cls, v)
    
    @validator('email')
    def validate_email(cls, v):
        """Validate and sanitize email format"""
        return SecurityValidators.validate_email(cls, v)
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
        return SecurityValidators.validate_password(cls, v)


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100, description="User's full name")
    email: Optional[str] = Field(None, max_length=254, description="User's email address")
    role: Optional[UserRole] = Field(None, description="User's role")
    is_active: Optional[bool] = Field(None, description="Whether user account is active")
    
    @validator('full_name')
    def validate_full_name(cls, v):
        """Validate and sanitize full name"""
        if v is not None:
            return SecurityValidators.validate_name(cls, v)
        return v
    
    @validator('email')
    def validate_email(cls, v):
        """Validate and sanitize email format"""
        if v is not None:
            return SecurityValidators.validate_email(cls, v)
        return v


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserListResponse(BaseModel):
    users: List[UserResponse]
    total: int
    page: int
    per_page: int
