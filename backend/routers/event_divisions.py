from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import List
from core.database import get_session
from services.event_division_service import EventDivisionService
from schemas.event_division import (
    EventDivisionCreate, EventDivisionUpdate, EventDivisionResponse, EventDivisionBulkCreate
)
from api.auth import get_current_user
from core.permissions import require_event_access, can_access_event
from models.user import User

router = APIRouter(prefix="/api/event-divisions", tags=["Event Divisions"])


@router.post("/", response_model=EventDivisionResponse)
def create_division(
    division_data: EventDivisionCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Create a new event division"""
    # Check if user has access to the event
    if not can_access_event(current_user, division_data.event_id, session):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this event"
        )
    
    try:
        service = EventDivisionService(session)
        division = service.create_division(division_data)
        return division
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/bulk", response_model=List[EventDivisionResponse])
def create_divisions_bulk(
    bulk_data: EventDivisionBulkCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Create multiple divisions for an event"""
    # Check if user has access to the event
    if not can_access_event(current_user, bulk_data.event_id, session):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this event"
        )
    
    try:
        service = EventDivisionService(session)
        divisions = service.create_divisions_bulk(bulk_data)
        return divisions
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/event/{event_id}", response_model=List[EventDivisionResponse])
def get_divisions_for_event(
    event_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get all divisions for an event"""
    # Check if user has access to the event
    if not can_access_event(current_user, event_id, session):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this event"
        )
    
    from models.participant import Participant
    from sqlmodel import select, func
    
    service = EventDivisionService(session)
    divisions = service.get_divisions_for_event(event_id)
    
    # Create response objects with participant count and teebox
    from models.course import Teebox
    from schemas.course import TeeboxResponse

    response_divisions = []
    for division in divisions:
        # Get participant count for this division
        participant_count = session.exec(
            select(func.count(Participant.id)).where(
                Participant.division_id == division.id
            )
        ).one()

        # Get teebox information if assigned
        teebox_data = None
        if division.teebox_id:
            teebox = session.get(Teebox, division.teebox_id)
            if teebox:
                teebox_data = TeeboxResponse.model_validate(teebox, from_attributes=True)

        # Create response object
        division_data = {
            "id": division.id,
            "event_id": division.event_id,
            "name": division.name,
            "description": division.description,
            "handicap_min": division.handicap_min,
            "handicap_max": division.handicap_max,
            "max_participants": division.max_participants,
            "teebox_id": division.teebox_id,
            "is_active": division.is_active,
            "created_at": division.created_at,
            "updated_at": division.updated_at,
            "participant_count": participant_count,
            "teebox": teebox_data
        }
        response_divisions.append(EventDivisionResponse.model_validate(division_data))

    return response_divisions


@router.get("/{division_id}", response_model=EventDivisionResponse)
def get_division(
    division_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get a specific division"""
    service = EventDivisionService(session)
    division = service.get_division(division_id)
    if not division:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Division not found")
    
    # Check if user has access to the event
    if not can_access_event(current_user, division.event_id, session):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this event"
        )
    
    return division


@router.put("/{division_id}", response_model=EventDivisionResponse)
def update_division(
    division_id: int,
    division_data: EventDivisionUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Update a division"""
    service = EventDivisionService(session)
    division = service.get_division(division_id)
    if not division:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Division not found")
    
    # Check if user has access to the event
    if not can_access_event(current_user, division.event_id, session):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this event"
        )
    
    try:
        division = service.update_division(division_id, division_data)
        return division
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{division_id}")
def delete_division(
    division_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Delete a division"""
    service = EventDivisionService(session)
    division = service.get_division(division_id)
    if not division:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Division not found")
    
    # Check if user has access to the event
    if not can_access_event(current_user, division.event_id, session):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this event"
        )
    
    success = service.delete_division(division_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Division not found")
    return {"message": "Division deleted successfully"}


@router.get("/event/{event_id}/stats")
def get_division_stats(
    event_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get division statistics for an event"""
    # Check if user has access to the event
    if not can_access_event(current_user, event_id, session):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this event"
        )

    service = EventDivisionService(session)
    stats = service.get_division_stats(event_id)
    return stats


# ==================== SUB-DIVISION ENDPOINTS ====================

@router.get("/event/{event_id}/tree")
def get_divisions_tree(
    event_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get hierarchical division structure for an event.
    Returns divisions with nested sub-divisions.
    """
    # Check if user has access to the event
    if not can_access_event(current_user, event_id, session):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this event"
        )

    service = EventDivisionService(session)
    divisions_tree = service.get_divisions_tree(event_id)
    return divisions_tree


@router.post("/subdivisions", response_model=EventDivisionResponse)
def create_subdivision(
    parent_division_id: int,
    name: str,
    handicap_min: float = None,
    handicap_max: float = None,
    description: str = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Create a sub-division under a parent division.
    For Net Stroke and System 36 Modified events.
    """
    try:
        service = EventDivisionService(session)

        # Get parent division to check access
        parent_division = service.get_division(parent_division_id)
        if not parent_division:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent division not found")

        # Check if user has access to the event
        if not can_access_event(current_user, parent_division.event_id, session):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this event"
            )

        subdivision = service.create_subdivision(
            parent_division_id=parent_division_id,
            name=name,
            handicap_min=handicap_min,
            handicap_max=handicap_max,
            description=description
        )
        return subdivision
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/subdivisions/{subdivision_id}")
def delete_subdivision(
    subdivision_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Delete a sub-division (only if no participants assigned)"""
    service = EventDivisionService(session)

    # Get subdivision to check access
    subdivision = service.get_division(subdivision_id)
    if not subdivision:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sub-division not found")

    # Check if user has access to the event
    if not can_access_event(current_user, subdivision.event_id, session):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this event"
        )

    try:
        success = service.delete_subdivision(subdivision_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sub-division not found")
        return {"message": "Sub-division deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/event/{event_id}/auto-assign-subdivisions")
def auto_assign_subdivisions(
    event_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Auto-assign participants to pre-defined sub-divisions based on declared handicap.
    For Net Stroke and System 36 Modified events.
    """
    # Check if user has access to the event
    if not can_access_event(current_user, event_id, session):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this event"
        )

    try:
        from services.participant_service import ParticipantService
        participant_service = ParticipantService(session)
        results = participant_service.auto_assign_to_subdivisions(event_id)
        return results
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
