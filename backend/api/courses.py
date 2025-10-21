from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select, func
from typing import List, Optional
from core.database import get_session
from models.course import Course, Hole
from models.user import User, UserRole
from schemas.course import CourseCreate, CourseUpdate, CourseResponse, CourseListResponse, HoleCreate, HoleResponse
from api.auth import get_current_user

router = APIRouter(prefix="/api/v1/courses", tags=["courses"])


@router.get("/", response_model=CourseListResponse)
async def get_courses(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get list of courses with pagination and search"""
    
    # Build query
    statement = select(Course)
    
    if search:
        statement = statement.where(
            Course.name.contains(search) | Course.location.contains(search)
        )
    
    # Get total count
    count_statement = select(func.count(Course.id))
    if search:
        count_statement = count_statement.where(
            Course.name.contains(search) | Course.location.contains(search)
        )
    
    total = session.exec(count_statement).one()
    
    # Apply pagination
    offset = (page - 1) * per_page
    statement = statement.offset(offset).limit(per_page)
    
    courses = session.exec(statement).all()
    
    # Convert to response format
    course_responses = []
    for course in courses:
        holes_statement = select(Hole).where(Hole.course_id == course.id).order_by(Hole.number)
        holes = session.exec(holes_statement).all()
        
        course_response = CourseResponse(
            id=course.id,
            name=course.name,
            location=course.location,
            total_holes=course.total_holes,
            created_at=course.created_at,
            updated_at=course.updated_at,
            holes=[HoleResponse.model_validate(hole, from_attributes=True) for hole in holes]
        )
        course_responses.append(course_response)
    
    return CourseListResponse(
        courses=course_responses,
        total=total,
        page=page,
        per_page=per_page
    )


@router.post("/", response_model=CourseResponse)
async def create_course(
    course_data: CourseCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Create a new course"""
    
    # Check permissions (event_admin and super_admin can create courses)
    if current_user.role not in [UserRole.EVENT_ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    # Create course
    course = Course(
        name=course_data.name,
        location=course_data.location,
        total_holes=course_data.total_holes
    )
    
    session.add(course)
    session.commit()
    session.refresh(course)
    
    # Create holes if provided
    if course_data.holes:
        for hole_data in course_data.holes:
            hole = Hole(
                course_id=course.id,
                number=hole_data.number,
                par=hole_data.par,
                handicap_index=hole_data.handicap_index,
                distance_meters=hole_data.distance_meters
            )
            session.add(hole)
        
        session.commit()
    
    # Get holes for response
    holes_statement = select(Hole).where(Hole.course_id == course.id).order_by(Hole.number)
    holes = session.exec(holes_statement).all()
    
    return CourseResponse(
        id=course.id,
        name=course.name,
        location=course.location,
        total_holes=course.total_holes,
        created_at=course.created_at,
        updated_at=course.updated_at,
        holes=[HoleResponse.model_validate(hole, from_attributes=True) for hole in holes]
    )


@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get course by ID"""
    
    statement = select(Course).where(Course.id == course_id)
    course = session.exec(statement).first()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Get holes
    holes_statement = select(Hole).where(Hole.course_id == course.id).order_by(Hole.number)
    holes = session.exec(holes_statement).all()
    
    return CourseResponse(
        id=course.id,
        name=course.name,
        location=course.location,
        total_holes=course.total_holes,
        created_at=course.created_at,
        updated_at=course.updated_at,
        holes=[HoleResponse.model_validate(hole, from_attributes=True) for hole in holes]
    )


@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: int,
    course_data: CourseUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Update course"""
    
    # Check permissions
    if current_user.role not in [UserRole.EVENT_ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    statement = select(Course).where(Course.id == course_id)
    course = session.exec(statement).first()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Update fields
    update_data = course_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(course, field, value)
    
    session.add(course)
    session.commit()
    session.refresh(course)
    
    # Get holes for response
    holes_statement = select(Hole).where(Hole.course_id == course.id).order_by(Hole.number)
    holes = session.exec(holes_statement).all()
    
    return CourseResponse(
        id=course.id,
        name=course.name,
        location=course.location,
        total_holes=course.total_holes,
        created_at=course.created_at,
        updated_at=course.updated_at,
        holes=[HoleResponse.model_validate(hole, from_attributes=True) for hole in holes]
    )


@router.delete("/{course_id}")
async def delete_course(
    course_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Delete course"""
    
    # Check permissions
    if current_user.role not in [UserRole.EVENT_ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    statement = select(Course).where(Course.id == course_id)
    course = session.exec(statement).first()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    session.delete(course)
    session.commit()
    
    return {"message": "Course deleted successfully"}


@router.get("/{course_id}/holes", response_model=List[HoleResponse])
async def get_course_holes(
    course_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get holes for a course"""
    
    # Verify course exists
    course_statement = select(Course).where(Course.id == course_id)
    course = session.exec(course_statement).first()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    holes_statement = select(Hole).where(Hole.course_id == course_id).order_by(Hole.number)
    holes = session.exec(holes_statement).all()
    
    return [HoleResponse.model_validate(hole, from_attributes=True) for hole in holes]


@router.post("/{course_id}/holes", response_model=List[HoleResponse])
async def update_course_holes(
    course_id: int,
    holes_data: List[HoleCreate],
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Update holes for a course"""
    
    # Check permissions
    if current_user.role not in [UserRole.EVENT_ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    # Verify course exists
    course_statement = select(Course).where(Course.id == course_id)
    course = session.exec(course_statement).first()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Delete existing holes
    existing_holes_statement = select(Hole).where(Hole.course_id == course_id)
    existing_holes = session.exec(existing_holes_statement).all()
    for hole in existing_holes:
        session.delete(hole)
    
    # Create new holes
    for hole_data in holes_data:
        hole = Hole(
            course_id=course_id,
            number=hole_data.number,
            par=hole_data.par,
            handicap_index=hole_data.handicap_index,
            distance_meters=hole_data.distance_meters
        )
        session.add(hole)
    
    session.commit()
    
    # Get updated holes
    holes_statement = select(Hole).where(Hole.course_id == course_id).order_by(Hole.number)
    holes = session.exec(holes_statement).all()
    
    return [HoleResponse.model_validate(hole, from_attributes=True) for hole in holes]
