from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from models.user import UserRole


class UserCreate(BaseModel):
    full_name: str
    email: str
    password: str
    role: UserRole = UserRole.EVENT_USER
    is_active: bool = True


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


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
