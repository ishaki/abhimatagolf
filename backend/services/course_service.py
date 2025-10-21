"""
Course service for business logic operations
"""
from typing import List, Optional
from sqlmodel import Session, select
from models.course import Course, Hole
from models.user import User
from schemas.course import CourseCreate, CourseUpdate, HoleCreate, HoleUpdate


class CourseService:
    def __init__(self, db: Session):
        self.db = db

    def create_course(self, course_data: CourseCreate, created_by: User) -> Course:
        """Create a new course"""
        db_course = Course(
            name=course_data.name,
            location=course_data.location,
            description=course_data.description,
            par_total=course_data.par_total,
            created_by_id=created_by.id
        )
        self.db.add(db_course)
        self.db.commit()
        self.db.refresh(db_course)
        return db_course

    def get_course(self, course_id: int) -> Optional[Course]:
        """Get course by ID"""
        return self.db.get(Course, course_id)

    def get_courses(self, skip: int = 0, limit: int = 100) -> List[Course]:
        """Get list of courses with pagination"""
        statement = select(Course).offset(skip).limit(limit)
        return list(self.db.exec(statement))

    def update_course(self, course_id: int, course_data: CourseUpdate) -> Optional[Course]:
        """Update course"""
        db_course = self.get_course(course_id)
        if not db_course:
            return None
        
        update_data = course_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_course, field, value)
        
        self.db.add(db_course)
        self.db.commit()
        self.db.refresh(db_course)
        return db_course

    def delete_course(self, course_id: int) -> bool:
        """Delete course"""
        db_course = self.get_course(course_id)
        if not db_course:
            return False
        
        self.db.delete(db_course)
        self.db.commit()
        return True

    def search_courses(self, search_term: str, skip: int = 0, limit: int = 100) -> List[Course]:
        """Search courses by name or location"""
        statement = select(Course).where(
            (Course.name.contains(search_term)) | 
            (Course.location.contains(search_term))
        ).offset(skip).limit(limit)
        return list(self.db.exec(statement))

    def get_course_holes(self, course_id: int) -> List[Hole]:
        """Get all holes for a course"""
        statement = select(Hole).where(Hole.course_id == course_id).order_by(Hole.hole_number)
        return list(self.db.exec(statement))

    def create_hole(self, course_id: int, hole_data: HoleCreate) -> Optional[Hole]:
        """Create a new hole for a course"""
        course = self.get_course(course_id)
        if not course:
            return None
        
        db_hole = Hole(
            course_id=course_id,
            hole_number=hole_data.hole_number,
            par=hole_data.par,
            handicap=hole_data.handicap,
            yardage=hole_data.yardage
        )
        self.db.add(db_hole)
        self.db.commit()
        self.db.refresh(db_hole)
        return db_hole

    def update_hole(self, hole_id: int, hole_data: HoleUpdate) -> Optional[Hole]:
        """Update hole"""
        db_hole = self.db.get(Hole, hole_id)
        if not db_hole:
            return None
        
        update_data = hole_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_hole, field, value)
        
        self.db.add(db_hole)
        self.db.commit()
        self.db.refresh(db_hole)
        return db_hole

    def delete_hole(self, hole_id: int) -> bool:
        """Delete hole"""
        db_hole = self.db.get(Hole, hole_id)
        if not db_hole:
            return False
        
        self.db.delete(db_hole)
        self.db.commit()
        return True

    def bulk_create_holes(self, course_id: int, holes_data: List[HoleCreate]) -> List[Hole]:
        """Create multiple holes for a course"""
        course = self.get_course(course_id)
        if not course:
            return []
        
        db_holes = []
        for hole_data in holes_data:
            db_hole = Hole(
                course_id=course_id,
                hole_number=hole_data.hole_number,
                par=hole_data.par,
                handicap=hole_data.handicap,
                yardage=hole_data.yardage
            )
            db_holes.append(db_hole)
            self.db.add(db_hole)
        
        self.db.commit()
        for db_hole in db_holes:
            self.db.refresh(db_hole)
        
        return db_holes
