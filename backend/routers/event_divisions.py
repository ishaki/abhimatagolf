from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import List
from core.database import get_session
from services.event_division_service import EventDivisionService
from schemas.event_division import (
    EventDivisionCreate, EventDivisionUpdate, EventDivisionResponse, EventDivisionBulkCreate
)

router = APIRouter(prefix="/api/event-divisions", tags=["Event Divisions"])


@router.post("/", response_model=EventDivisionResponse)
def create_division(
    division_data: EventDivisionCreate,
    session: Session = Depends(get_session)
):
    """Create a new event division"""
    try:
        service = EventDivisionService(session)
        division = service.create_division(division_data)
        return division
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/bulk", response_model=List[EventDivisionResponse])
def create_divisions_bulk(
    bulk_data: EventDivisionBulkCreate,
    session: Session = Depends(get_session)
):
    """Create multiple divisions for an event"""
    try:
        service = EventDivisionService(session)
        divisions = service.create_divisions_bulk(bulk_data)
        return divisions
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/event/{event_id}", response_model=List[EventDivisionResponse])
def get_divisions_for_event(
    event_id: int,
    session: Session = Depends(get_session)
):
    """Get all divisions for an event"""
    from models.participant import Participant
    from sqlmodel import select, func
    
    service = EventDivisionService(session)
    divisions = service.get_divisions_for_event(event_id)
    
    # Create response objects with participant count
    response_divisions = []
    for division in divisions:
        # Get participant count for this division
        participant_count = session.exec(
            select(func.count(Participant.id)).where(
                Participant.division_id == division.id
            )
        ).one()
        
        # Create response object
        division_data = {
            "id": division.id,
            "event_id": division.event_id,
            "name": division.name,
            "description": division.description,
            "handicap_min": division.handicap_min,
            "handicap_max": division.handicap_max,
            "max_participants": division.max_participants,
            "is_active": division.is_active,
            "created_at": division.created_at,
            "updated_at": division.updated_at,
            "participant_count": participant_count
        }
        response_divisions.append(EventDivisionResponse.model_validate(division_data))
    
    return response_divisions


@router.get("/{division_id}", response_model=EventDivisionResponse)
def get_division(
    division_id: int,
    session: Session = Depends(get_session)
):
    """Get a specific division"""
    service = EventDivisionService(session)
    division = service.get_division(division_id)
    if not division:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Division not found")
    return division


@router.put("/{division_id}", response_model=EventDivisionResponse)
def update_division(
    division_id: int,
    division_data: EventDivisionUpdate,
    session: Session = Depends(get_session)
):
    """Update a division"""
    try:
        service = EventDivisionService(session)
        division = service.update_division(division_id, division_data)
        if not division:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Division not found")
        return division
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{division_id}")
def delete_division(
    division_id: int,
    session: Session = Depends(get_session)
):
    """Delete a division"""
    service = EventDivisionService(session)
    success = service.delete_division(division_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Division not found")
    return {"message": "Division deleted successfully"}


@router.get("/event/{event_id}/stats")
def get_division_stats(
    event_id: int,
    session: Session = Depends(get_session)
):
    """Get division statistics for an event"""
    service = EventDivisionService(session)
    stats = service.get_division_stats(event_id)
    return stats
