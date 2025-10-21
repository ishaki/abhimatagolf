from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session
from typing import Optional
from core.database import get_session
from core.security import get_current_user
from services.leaderboard_service import LeaderboardService
from schemas.leaderboard import (
    LeaderboardResponse,
    PublicLeaderboardResponse,
    LeaderboardFilter,
    LeaderboardStats
)
from models.user import User

router = APIRouter(prefix="/api/v1/leaderboards", tags=["Leaderboards"])


def get_leaderboard_service(session: Session = Depends(get_session)) -> LeaderboardService:
    """Dependency to get leaderboard service"""
    return LeaderboardService(session)


@router.get("/event/{event_id}", response_model=LeaderboardResponse)
async def get_event_leaderboard(
    event_id: int,
    division_id: Optional[int] = Query(None, description="Filter by division ID"),
    division_name: Optional[str] = Query(None, description="Filter by division name"),
    min_holes: Optional[int] = Query(None, description="Minimum holes completed"),
    max_rank: Optional[int] = Query(None, description="Maximum rank to show"),
    use_cache: bool = Query(True, description="Use cached data if available"),
    current_user: User = Depends(get_current_user),
    service: LeaderboardService = Depends(get_leaderboard_service)
):
    """
    Get leaderboard for an event
    
    **Required permissions**: authenticated user
    
    Args:
        - event_id: Event ID
        - division_id: Optional division filter
        - division_name: Optional division name filter
        - min_holes: Minimum holes completed filter
        - max_rank: Maximum rank to show
        - use_cache: Whether to use cached data
        
    Returns:
        - Complete leaderboard with rankings and scores
    """
    try:
        filter_options = LeaderboardFilter(
            division_id=division_id,
            division_name=division_name,
            min_holes=min_holes,
            max_rank=max_rank
        )
        
        leaderboard = service.calculate_leaderboard(
            event_id=event_id,
            filter_options=filter_options,
            use_cache=use_cache
        )
        
        return leaderboard
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate leaderboard: {str(e)}")


@router.get("/event/{event_id}/stats", response_model=LeaderboardStats)
async def get_leaderboard_stats(
    event_id: int,
    current_user: User = Depends(get_current_user),
    service: LeaderboardService = Depends(get_leaderboard_service)
):
    """
    Get leaderboard statistics for an event
    
    **Required permissions**: authenticated user
    
    Args:
        - event_id: Event ID
        
    Returns:
        - Leaderboard statistics (averages, cut line, etc.)
    """
    try:
        stats = service.get_leaderboard_stats(event_id)
        return stats
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get leaderboard stats: {str(e)}")


@router.post("/event/{event_id}/invalidate-cache")
async def invalidate_leaderboard_cache(
    event_id: int,
    current_user: User = Depends(get_current_user),
    service: LeaderboardService = Depends(get_leaderboard_service)
):
    """
    Invalidate leaderboard cache for an event
    
    **Required permissions**: super_admin or event_admin
    
    Args:
        - event_id: Event ID
        
    Returns:
        - Success message
    """
    # Check permissions
    if current_user.role not in ["super_admin", "event_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to invalidate cache"
        )
    
    try:
        service.invalidate_cache(event_id)
        return {"message": f"Leaderboard cache invalidated for event {event_id}"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to invalidate cache: {str(e)}")


# Public endpoints (no authentication required)
@router.get("/public/event/{event_id}", response_model=PublicLeaderboardResponse)
async def get_public_leaderboard(
    event_id: int,
    division_id: Optional[int] = Query(None, description="Filter by division ID"),
    division_name: Optional[str] = Query(None, description="Filter by division name"),
    min_holes: Optional[int] = Query(None, description="Minimum holes completed"),
    max_rank: Optional[int] = Query(None, description="Maximum rank to show"),
    service: LeaderboardService = Depends(get_leaderboard_service)
):
    """
    Get public leaderboard for an event (no authentication required)
    
    Args:
        - event_id: Event ID
        - division_id: Optional division filter
        - division_name: Optional division name filter
        - min_holes: Minimum holes completed filter
        - max_rank: Maximum rank to show
        
    Returns:
        - Public leaderboard data
    """
    try:
        filter_options = LeaderboardFilter(
            division_id=division_id,
            division_name=division_name,
            min_holes=min_holes,
            max_rank=max_rank
        )
        
        leaderboard = service.calculate_leaderboard(
            event_id=event_id,
            filter_options=filter_options,
            use_cache=True
        )
        
        # Convert to public response (remove sensitive data)
        public_response = PublicLeaderboardResponse(
            event_id=leaderboard.event_id,
            event_name=leaderboard.event_name,
            course_name=leaderboard.course_name,
            scoring_type=leaderboard.scoring_type,
            entries=leaderboard.entries,
            total_participants=leaderboard.total_participants,
            last_updated=leaderboard.last_updated
        )
        
        return public_response
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get public leaderboard: {str(e)}")
