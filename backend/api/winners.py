from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from core.database import get_session
from core.security import get_current_user
from core.permissions import require_event_admin_or_super, can_access_winners, can_modify_event
from models.user import User
from models.event import Event
from models.winner_result import WinnerResult
from schemas.winner import (
    WinnerResultResponse,
    CalculateWinnersRequest,
    WinnersListResponse
)
from schemas.winner_configuration import (
    WinnerConfigurationCreate,
    WinnerConfigurationUpdate,
    WinnerConfigurationResponse,
    WinnerManualOverride
)
from services.winner_service import WinnerService
from services.winner_configuration_service import WinnerConfigurationService
from typing import List, Optional
from core.app_logging import logger

router = APIRouter(prefix="/api/v1/winners", tags=["winners"])


@router.post("/calculate", response_model=List[WinnerResultResponse])
def calculate_event_winners(
    request: CalculateWinnersRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Calculate winners for an event.
    Requires EVENT_ADMIN (for events they created) or SUPER_ADMIN role.
    """
    # Check if user can modify this event
    if not can_modify_event(current_user, request.event_id, session):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to calculate winners for this event"
        )
    
    # Get event to verify it exists
    event = session.get(Event, request.event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event {request.event_id} not found"
        )

    try:
        winners = WinnerService.calculate_winners(session, request.event_id, current_user.id)
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
        scoring_type=event.scoring_type.value,  # Include scoring type for conditional display
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
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Get winners for an event (admin view).
    Requires EVENT_ADMIN (for events they created) or SUPER_ADMIN role.
    """
    # Check if user can modify this event
    if not can_modify_event(current_user, event_id, session):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view winners for this event"
        )

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
        scoring_type=event.scoring_type.value,  # Include scoring type for conditional display
        total_winners=len(winners),
        winners=winners
    )


# ===== Winner Configuration Endpoints =====

@router.get("/config/{event_id}", response_model=WinnerConfigurationResponse)
def get_winner_config(
    event_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Get winner configuration for an event.
    Requires EVENT_ADMIN (for events they created) or SUPER_ADMIN role.

    If configuration doesn't exist, creates a default one.
    """
    # Check if user can modify this event
    if not can_modify_event(current_user, event_id, session):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view winner configuration for this event"
        )
    
    # Verify event exists
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event {event_id} not found"
        )

    # Get or create configuration
    config = WinnerConfigurationService.get_or_create_config(
        session,
        event_id,
        current_user.id
    )

    logger.info(f"User {current_user.id} retrieved winner config for event {event_id}")
    return config


@router.post("/config", response_model=WinnerConfigurationResponse, status_code=status.HTTP_201_CREATED)
def create_winner_config(
    config_data: WinnerConfigurationCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Create winner configuration for an event.
    Requires EVENT_ADMIN (for events they created) or SUPER_ADMIN role.

    Returns 400 if configuration already exists.
    """
    # Check if user can modify this event
    if not can_modify_event(current_user, config_data.event_id, session):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to create winner configuration for this event"
        )
    
    try:
        config = WinnerConfigurationService.create_config(
            session,
            config_data,
            current_user.id
        )
        logger.info(f"User {current_user.id} created winner config for event {config_data.event_id}")
        return config
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/config/{event_id}", response_model=WinnerConfigurationResponse)
def update_winner_config(
    event_id: int,
    config_update: WinnerConfigurationUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Update winner configuration for an event.
    Requires EVENT_ADMIN (for events they created) or SUPER_ADMIN role.

    Returns 404 if configuration doesn't exist.
    """
    # Check if user can modify this event
    if not can_modify_event(current_user, event_id, session):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update winner configuration for this event"
        )
    
    # Verify event exists
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event {event_id} not found"
        )

    config = WinnerConfigurationService.update_config(session, event_id, config_update)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Winner configuration not found for event {event_id}"
        )

    logger.info(f"User {current_user.id} updated winner config for event {event_id}")
    return config


@router.delete("/config/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_winner_config(
    event_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Delete winner configuration for an event.
    Requires EVENT_ADMIN (for events they created) or SUPER_ADMIN role.

    Returns 404 if configuration doesn't exist.
    """
    # Check if user can modify this event
    if not can_modify_event(current_user, event_id, session):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete winner configuration for this event"
        )
    
    deleted = WinnerConfigurationService.delete_config(session, event_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Winner configuration not found for event {event_id}"
        )

    logger.info(f"User {current_user.id} deleted winner config for event {event_id}")
    return None


# ===== Manual Override Endpoints =====

@router.patch("/{winner_id}/override", response_model=WinnerResultResponse)
def override_winner_result(
    winner_id: int,
    override_data: WinnerManualOverride,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Manually override winner result fields.
    Requires EVENT_ADMIN (for events they created) or SUPER_ADMIN role.

    Only allows override if event configuration permits it.
    """
    # Get winner result
    winner = session.get(WinnerResult, winner_id)
    if not winner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Winner result {winner_id} not found"
        )

    # Check if user can modify this event
    if not can_modify_event(current_user, winner.event_id, session):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to override winner results for this event"
        )

    # Check if manual override is allowed
    config = WinnerConfigurationService.get_config_by_event(session, winner.event_id)
    if config and not config.allow_manual_override:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manual override is not allowed for this event"
        )

    # Apply overrides
    update_data = override_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(winner, key, value)

    session.add(winner)
    session.commit()
    session.refresh(winner)

    logger.info(
        f"User {current_user.id} manually overrode winner {winner_id} for event {winner.event_id}",
        extra={"security_event": True}
    )
    return winner


@router.delete("/{winner_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_winner_result(
    winner_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Delete a winner result.
    Requires EVENT_ADMIN (for events they created) or SUPER_ADMIN role.

    Use this to remove incorrectly calculated results.
    """
    # Get winner result
    winner = session.get(WinnerResult, winner_id)
    if not winner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Winner result {winner_id} not found"
        )

    # Check if user can modify this event
    if not can_modify_event(current_user, winner.event_id, session):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete winner results for this event"
        )

    event_id = winner.event_id
    session.delete(winner)
    session.commit()

    logger.info(
        f"User {current_user.id} deleted winner {winner_id} from event {event_id}",
        extra={"security_event": True}
    )
    return None


@router.get("/{event_id}/export")
def export_participant_scores(
    event_id: int,
    session: Session = Depends(get_session)
):
    """
    Export participant scores to Excel file.
    Public endpoint - no authentication required.
    
    Returns Excel file with three sheets:
    1. Scores: Participant, Hole 1-9, Total Out, Hole 10-18, Total In, Total (showing scores)
    2. Points: Participant, Hole 1-9, Total Out, Hole 10-18, Total In, Total Point (showing System 36 points)
    3. Summary: Participant, Declared Hcp, Course Handicap, Total Gross, Nett, Total Point
    """
    from services.excel_service import ExcelService
    from fastapi.responses import StreamingResponse
    from io import BytesIO
    from datetime import datetime
    
    # Get event
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event {event_id} not found"
        )

    try:
        # Create Excel service and export data
        excel_service = ExcelService(session)
        excel_file = excel_service.export_participant_scores_detailed(event_id)
        
        # Generate filename
        event_name_clean = "".join(c for c in event.name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        current_date = datetime.now().strftime("%Y%m%d")
        filename = f"{event_name_clean}_Scores_{current_date}.xlsx"
        
        # Return file as streaming response
        excel_file.seek(0)
        return StreamingResponse(
            BytesIO(excel_file.read()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Error exporting scores for event {event_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export participant scores"
        )