from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime


class Course(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=200)
    location: Optional[str] = Field(default=None, max_length=300)
    total_holes: int = Field(default=18)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    holes: List["Hole"] = Relationship(back_populates="course")
    events: List["Event"] = Relationship(back_populates="course")


class Hole(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    course_id: int = Field(foreign_key="course.id")
    number: int = Field()
    par: int = Field()
    handicap_index: int = Field()
    distance_meters: Optional[float] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    course: Course = Relationship(back_populates="holes")
    scorecards: List["Scorecard"] = Relationship(back_populates="hole")
    
    class Config:
        # Ensure unique hole number per course
        # Note: unique_together is not supported in SQLModel
        # Use database constraints instead
        pass
