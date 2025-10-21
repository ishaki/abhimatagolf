from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session
from typing import Optional, List
from datetime import date
from core.database import get_session
from core.security import get_current_user
from services.event_service import EventService
from schemas.event import EventCreate, EventUpdate, EventResponse, EventListResponse, EventStats
from models.user import User
from models.event import ScoringType

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/", response_model=EventListResponse)
async def get_events(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    course_id: Optional[int] = Query(None),
    scoring_type: Optional[ScoringType] = Query(None),
    is_active: Optional[bool] = Query(None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get events with filtering and pagination"""
    event_service = EventService(session)
    events, total = event_service.get_events(
        page=page,
        per_page=per_page,
        search=search,
        course_id=course_id,
        scoring_type=scoring_type,
        is_active=is_active,
        created_by=current_user.id if current_user.role == "event_admin" else None
    )
    
    # Convert to response format
    event_responses = []
    for event in events:
        event_response = event_service.get_event_with_details(event.id)
        if event_response:
            event_responses.append(event_response)
    
    return EventListResponse(
        events=event_responses,
        total=total,
        page=page,
        per_page=per_page
    )


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get single event by ID"""
    event_service = EventService(session)
    event = event_service.get_event_with_details(event_id)
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return event


@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    event_data: EventCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Create new event"""
    # Check permissions
    if current_user.role not in ["super_admin", "event_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Insufficient permissions"
        )
    
    event_service = EventService(session)
    event = event_service.create_event(event_data, current_user.id)
    
    return event_service.get_event_with_details(event.id)


@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: int,
    event_data: EventUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Update event"""
    event_service = EventService(session)
    event = event_service.get_event(event_id)
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check permissions
    if current_user.role == "event_admin" and event.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Can only edit your own events"
        )
    
    updated_event = event_service.update_event(event_id, event_data)
    return event_service.get_event_with_details(event_id)


@router.delete("/{event_id}")
async def delete_event(
    event_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Delete event"""
    event_service = EventService(session)
    event = event_service.get_event(event_id)
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check permissions
    if current_user.role == "event_admin" and event.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Can only delete your own events"
        )
    
    success = event_service.delete_event(event_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Failed to delete event"
        )
    
    return {"message": "Event deleted successfully"}


@router.get("/stats/overview", response_model=EventStats)
async def get_event_stats(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get event statistics"""
    event_service = EventService(session)
    return event_service.get_event_stats()


@router.post("/{event_id}/duplicate", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def duplicate_event(
    event_id: int,
    new_name: str,
    new_date: date,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Duplicate an existing event"""
    event_service = EventService(session)
    original_event = event_service.get_event(event_id)
    
    if not original_event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check permissions
    if current_user.role == "event_admin" and original_event.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Can only duplicate your own events"
        )
    
    new_event = event_service.duplicate_event(event_id, new_name, new_date)
    if not new_event:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Failed to duplicate event"
        )
    
    return event_service.get_event_with_details(new_event.id)
