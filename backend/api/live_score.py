"""
Live Score API - Phase 3.2

Public API endpoint for real-time tournament score display.
No authentication required - designed for TV/projector display.
"""

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from typing import List
from core.database import get_session
from services.live_score_service import LiveScoreService
from schemas.scorecard import ScorecardResponse


router = APIRouter(prefix="/api/v1/live-score", tags=["Live Score"])


def get_live_score_service(session: Session = Depends(get_session)) -> LiveScoreService:
    """Dependency to get live score service"""
    return LiveScoreService(session)


@router.get("/{event_id}", response_model=List[ScorecardResponse])
async def get_live_score(
    event_id: int,
    sort_by: str = Query(
        "gross",
        description="Sort method: 'gross' or 'net' (Phase 3: both use gross)",
        regex="^(gross|net)$"
    ),
    filter_empty: bool = Query(
        False,
        description="If True, exclude participants with no hole scores entered"
    ),
    service: LiveScoreService = Depends(get_live_score_service),
):
    """
    Get live score data for an event (PUBLIC - No authentication required)

    **Purpose**: Display real-time scores on TV/projector or web for tournament viewers

    **Returns**:
    - All participants with raw scorecard data
    - Hole-by-hole strokes (no calculations)
    - Sorted by: holes completed → gross score → zeros last

    **Parameters**:
    - `sort_by`: Sort method - "gross" or "net" (Phase 3: both use gross)
    - `filter_empty`: If True, exclude participants with no hole scores entered

    **Phase 3 Note**:
    - `sort_by` parameter accepts "gross" or "net", but both currently sort by gross
    - Net scoring will be enabled after Winner Page calculations are implemented

    **Caching**: Results cached for 30 seconds for performance

    **Use Case**:
    - Public leaderboard displays
    - Tournament TV screens
    - Spectator web views
    - Mobile apps
    """
    return service.get_live_score(event_id=event_id, sort_by=sort_by, filter_empty=filter_empty)
