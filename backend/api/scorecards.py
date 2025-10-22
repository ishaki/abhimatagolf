from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlmodel import Session
from typing import List
from core.database import get_session
from core.security import get_current_user
from core.audit_logging import get_audit_logger, AuditAction
from core.permissions import can_manage_scores
from models.user import User, UserRole
from models.participant import Participant
from services.scorecard_service import ScorecardService
from schemas.scorecard import (
    HoleScoreInput,
    ScorecardSubmit,
    HoleScoreResponse,
    ScorecardResponse,
    ScorecardListResponse,
    ScoreUpdate,
    ScoreHistoryResponse,
)

router = APIRouter(prefix="/api/v1/scorecards", tags=["Scorecards"])


def get_scorecard_service(session: Session = Depends(get_session)) -> ScorecardService:
    """Dependency to get scorecard service"""
    service = ScorecardService(session)
    # Set live scoring service reference if available
    from main import live_scoring_service
    if live_scoring_service:
        service.set_live_scoring_service(live_scoring_service)
    return service


def check_scoring_permission(current_user: User, event_id: int, session: Session) -> None:
    """
    Check if user has permission to enter/edit scores for a specific event

    Args:
        current_user: The current user
        event_id: The ID of the event
        session: Database session
    """
    if not can_manage_scores(current_user, event_id, session):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to manage scores for this event",
        )


@router.post("/", response_model=HoleScoreResponse, status_code=status.HTTP_201_CREATED)
async def submit_hole_score(
    participant_id: int,
    hole_number: int,
    strokes: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    service: ScorecardService = Depends(get_scorecard_service),
    session: Session = Depends(get_session),
):
    """
    Submit or update a score for a single hole

    **Required permissions**: super_admin, event_admin, or event_user assigned to the event

    Args:
        - participant_id: ID of the participant
        - hole_number: Hole number (1-18)
        - strokes: Number of strokes (1-15)

    Returns:
        - HoleScoreResponse with score details and color coding
    """
    audit_logger = get_audit_logger()
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    # Get participant to determine event_id
    participant = session.get(Participant, participant_id)
    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Participant {participant_id} not found",
        )
    
    # Check permissions for the specific event
    check_scoring_permission(current_user, participant.event_id, session)

    try:
        result = await service.submit_hole_score(
            participant_id=participant_id,
            hole_number=hole_number,
            strokes=strokes,
            user_id=current_user.id,
        )
        
        # Log successful score submission
        audit_logger.log_user_action(
            action=AuditAction.SCORE_SUBMIT,
            user_id=current_user.id,
            user_email=current_user.email,
            user_role=current_user.role,
            resource_type="score",
            resource_id=result.id,
            description=f"Submitted score: {strokes} strokes for hole {hole_number}, participant {participant_id}",
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        return result
        
    except Exception as e:
        # Log failed score submission
        audit_logger.log_user_action(
            action=AuditAction.SCORE_SUBMIT,
            user_id=current_user.id,
            user_email=current_user.email,
            user_role=current_user.role,
            resource_type="score",
            description=f"Failed to submit score: {strokes} strokes for hole {hole_number}, participant {participant_id}",
            ip_address=client_ip,
            user_agent=user_agent,
            success=False,
            error_message=str(e)
        )
        raise


@router.post("/bulk", response_model=ScorecardResponse, status_code=status.HTTP_201_CREATED)
async def bulk_submit_scores(
    data: ScorecardSubmit,
    current_user: User = Depends(get_current_user),
    service: ScorecardService = Depends(get_scorecard_service),
    session: Session = Depends(get_session),
):
    """
    Submit scores for multiple holes at once

    **Required permissions**: super_admin, event_admin, or event_user assigned to the event

    Args:
        - data: ScorecardSubmit with participant_id and list of hole scores

    Returns:
        - Complete ScorecardResponse with all calculations
    """
    # Get participant to determine event_id
    participant = session.get(Participant, data.participant_id)
    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Participant {data.participant_id} not found",
        )
    
    # Check permissions for the specific event
    check_scoring_permission(current_user, participant.event_id, session)

    return await service.bulk_submit_scores(data=data, user_id=current_user.id)


@router.get("/participant/{participant_id}", response_model=ScorecardResponse)
async def get_participant_scorecard(
    participant_id: int,
    current_user: User = Depends(get_current_user),
    service: ScorecardService = Depends(get_scorecard_service),
):
    """
    Get complete scorecard for a participant

    **Required permissions**: authenticated user

    Args:
        - participant_id: ID of the participant

    Returns:
        - Complete ScorecardResponse with front nine, back nine, and totals
    """
    return service.get_participant_scorecard(participant_id)


@router.get("/event/{event_id}", response_model=ScorecardListResponse)
async def get_event_scorecards(
    event_id: int,
    current_user: User = Depends(get_current_user),
    service: ScorecardService = Depends(get_scorecard_service),
):
    """
    Get scorecards for all participants in an event

    **Required permissions**: authenticated user

    Args:
        - event_id: ID of the event

    Returns:
        - List of ScorecardResponse for all participants
    """
    scorecards = service.get_event_scorecards(event_id)

    return ScorecardListResponse(
        scorecards=scorecards,
        total=len(scorecards),
    )


@router.put("/{scorecard_id}", response_model=HoleScoreResponse)
async def update_hole_score(
    scorecard_id: int,
    data: ScoreUpdate,
    current_user: User = Depends(get_current_user),
    service: ScorecardService = Depends(get_scorecard_service),
    session: Session = Depends(get_session),
):
    """
    Update an existing hole score

    **Required permissions**: super_admin, event_admin, or event_user assigned to the event

    Args:
        - scorecard_id: ID of the scorecard to update
        - data: ScoreUpdate with new strokes and optional reason

    Returns:
        - Updated HoleScoreResponse
    """
    # Get scorecard to determine event_id
    from models.scorecard import Scorecard
    scorecard = session.get(Scorecard, scorecard_id)
    if not scorecard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scorecard {scorecard_id} not found",
        )
    
    # Check permissions for the specific event
    check_scoring_permission(current_user, scorecard.event_id, session)

    return service.update_hole_score(
        scorecard_id=scorecard_id,
        data=data,
        user_id=current_user.id,
    )


@router.delete("/{scorecard_id}", status_code=status.HTTP_200_OK)
async def delete_hole_score(
    scorecard_id: int,
    current_user: User = Depends(get_current_user),
    service: ScorecardService = Depends(get_scorecard_service),
    session: Session = Depends(get_session),
):
    """
    Delete a hole score

    **Required permissions**: super_admin, event_admin, or event_user assigned to the event

    Args:
        - scorecard_id: ID of the scorecard to delete

    Returns:
        - Success message
    """
    # Get scorecard to determine event_id
    from models.scorecard import Scorecard
    scorecard = session.get(Scorecard, scorecard_id)
    if not scorecard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scorecard {scorecard_id} not found",
        )
    
    # Check permissions for the specific event
    check_scoring_permission(current_user, scorecard.event_id, session)

    return service.delete_hole_score(scorecard_id=scorecard_id, user_id=current_user.id)


@router.get("/{scorecard_id}/history", response_model=List[ScoreHistoryResponse])
async def get_score_history(
    scorecard_id: int,
    current_user: User = Depends(get_current_user),
    service: ScorecardService = Depends(get_scorecard_service),
    session: Session = Depends(get_session),
):
    """
    Get score change history for a scorecard

    **Required permissions**: super_admin, event_admin, or event_user assigned to the event

    Args:
        - scorecard_id: ID of the scorecard

    Returns:
        - List of ScoreHistoryResponse entries ordered by most recent first
    """
    # Get scorecard to determine event_id
    from models.scorecard import Scorecard
    scorecard = session.get(Scorecard, scorecard_id)
    if not scorecard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scorecard {scorecard_id} not found",
        )
    
    # Check permissions for the specific event
    check_scoring_permission(current_user, scorecard.event_id, session)

    return service.get_score_history(scorecard_id)
