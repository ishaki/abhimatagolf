from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from models.course import Course, Hole


class HoleCreate(BaseModel):
    number: int
    par: int
    handicap_index: int
    distance_meters: Optional[float] = None


class HoleUpdate(BaseModel):
    number: Optional[int] = None
    par: Optional[int] = None
    handicap_index: Optional[int] = None
    distance_meters: Optional[float] = None


class HoleResponse(BaseModel):
    id: int
    course_id: int
    number: int
    par: int
    handicap_index: int
    distance_meters: Optional[float]
    created_at: datetime


class CourseCreate(BaseModel):
    name: str
    location: Optional[str] = None
    total_holes: int = 18
    holes: Optional[List[HoleCreate]] = None


class CourseUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    total_holes: Optional[int] = None


class CourseResponse(BaseModel):
    id: int
    name: str
    location: Optional[str]
    total_holes: int
    created_at: datetime
    updated_at: datetime
    holes: List[HoleResponse] = []


class CourseListResponse(BaseModel):
    courses: List[CourseResponse]
    total: int
    page: int
    per_page: int
