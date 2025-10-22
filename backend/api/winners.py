from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from core.database import get_session
from core.security import get_current_user
from core.permissions import require_event_admin_or_super, can_access_winners
from models.user import User
from models.event import Event
from schemas.winner import (
    WinnerResultResponse,
    CalculateWinnersRequest,
    WinnersListResponse
)
from services.winner_service import WinnerService
from typing import List, Optional

router = APIRouter(prefix="/api/v1/winners", tags=["winners"])


@router.post("/calculate", response_model=List[WinnerResultResponse])
def calculate_event_winners(
    request: CalculateWinnersRequest,
    current_user: User = Depends(require_event_admin_or_super()),
    session: Session = Depends(get_session)
):
    """
    Calculate winners for an event.
    Requires EVENT_ADMIN or SUPER_ADMIN role.
    """
    # Get event to verify it exists
    event = session.get(Event, request.event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event {request.event_id} not found"
        )

    try:
        winners = WinnerService.calculate_winners(session, request.event_id)
        return winners
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{event_id}", response_model=WinnersListResponse)
def get_event_winners(
    event_id: int,
    division_id: Optional[int] = None,
    top_n: Optional[int] = None,
    session: Session = Depends(get_session)
):
    """
    Get winners for an event.
    Public endpoint - no authentication required.

    Args:
        event_id: Event ID
        division_id: Optional filter by division
        top_n: Optional limit to top N winners
    """
    # Get event
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event {event_id} not found"
        )

    # Get winners
    winners = WinnerService.get_winners(
        session,
        event_id,
        division_id=division_id,
        top_n=top_n
    )

    return WinnersListResponse(
        event_id=event_id,
        event_name=event.name,
        total_winners=len(winners),
        winners=winners
    )


@router.get("/{event_id}/overall-winner", response_model=Optional[WinnerResultResponse])
def get_overall_winner(
    event_id: int,
    session: Session = Depends(get_session)
):
    """
    Get the overall winner (rank 1) for an event.
    Public endpoint - no authentication required.
    """
    # Get event
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event {event_id} not found"
        )

    winner = WinnerService.get_overall_winner(session, event_id)

    if not winner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No winner calculated for event {event_id}"
        )

    return winner


@router.get("/{event_id}/division/{division_id}/winner", response_model=Optional[WinnerResultResponse])
def get_division_winner(
    event_id: int,
    division_id: int,
    session: Session = Depends(get_session)
):
    """
    Get the winner for a specific division.
    Public endpoint - no authentication required.
    """
    # Get event
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event {event_id} not found"
        )

    winner = WinnerService.get_division_winner(session, event_id, division_id)

    if not winner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No winner calculated for division {division_id} in event {event_id}"
        )

    return winner


@router.get("/{event_id}/admin", response_model=WinnersListResponse)
def get_event_winners_admin(
    event_id: int,
    division_id: Optional[int] = None,
    top_n: Optional[int] = None,
    current_user: User = Depends(require_event_admin_or_super()),
    session: Session = Depends(get_session)
):
    """
    Get winners for an event (admin view).
    Requires EVENT_ADMIN or SUPER_ADMIN role.
    """
    # Get event
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event {event_id} not found"
        )

    # Get winners
    winners = WinnerService.get_winners(
        session,
        event_id,
        division_id=division_id,
        top_n=top_n
    )

    return WinnersListResponse(
        event_id=event_id,
        event_name=event.name,
        total_winners=len(winners),
        winners=winners
    )
