from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import List
from core.database import get_session
from core.security import get_current_user
from models.user import User, UserRole
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


def check_scoring_permission(current_user: User) -> None:
    """
    Check if user has permission to enter/edit scores

    Only super_admin and event_admin can enter scores
    """
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.EVENT_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to enter scores",
        )


@router.post("/", response_model=HoleScoreResponse, status_code=status.HTTP_201_CREATED)
async def submit_hole_score(
    participant_id: int,
    hole_number: int,
    strokes: int,
    current_user: User = Depends(get_current_user),
    service: ScorecardService = Depends(get_scorecard_service),
):
    """
    Submit or update a score for a single hole

    **Required permissions**: super_admin or event_admin

    Args:
        - participant_id: ID of the participant
        - hole_number: Hole number (1-18)
        - strokes: Number of strokes (1-15)

    Returns:
        - HoleScoreResponse with score details and color coding
    """
    check_scoring_permission(current_user)

    return await service.submit_hole_score(
        participant_id=participant_id,
        hole_number=hole_number,
        strokes=strokes,
        user_id=current_user.id,
    )


@router.post("/bulk", response_model=ScorecardResponse, status_code=status.HTTP_201_CREATED)
async def bulk_submit_scores(
    data: ScorecardSubmit,
    current_user: User = Depends(get_current_user),
    service: ScorecardService = Depends(get_scorecard_service),
):
    """
    Submit scores for multiple holes at once

    **Required permissions**: super_admin or event_admin

    Args:
        - data: ScorecardSubmit with participant_id and list of hole scores

    Returns:
        - Complete ScorecardResponse with all calculations
    """
    check_scoring_permission(current_user)

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
):
    """
    Update an existing hole score

    **Required permissions**: super_admin or event_admin

    Args:
        - scorecard_id: ID of the scorecard to update
        - data: ScoreUpdate with new strokes and optional reason

    Returns:
        - Updated HoleScoreResponse
    """
    check_scoring_permission(current_user)

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
):
    """
    Delete a hole score

    **Required permissions**: super_admin or event_admin

    Args:
        - scorecard_id: ID of the scorecard to delete

    Returns:
        - Success message
    """
    check_scoring_permission(current_user)

    return service.delete_hole_score(scorecard_id=scorecard_id, user_id=current_user.id)


@router.get("/{scorecard_id}/history", response_model=List[ScoreHistoryResponse])
async def get_score_history(
    scorecard_id: int,
    current_user: User = Depends(get_current_user),
    service: ScorecardService = Depends(get_scorecard_service),
):
    """
    Get score change history for a scorecard

    **Required permissions**: super_admin or event_admin

    Args:
        - scorecard_id: ID of the scorecard

    Returns:
        - List of ScoreHistoryResponse entries ordered by most recent first
    """
    check_scoring_permission(current_user)

    return service.get_score_history(scorecard_id)
