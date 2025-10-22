from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import List, Optional
from pydantic import BaseModel
from core.database import get_session
from core.security import get_current_user
from models.user import User
from models.participant import Participant
from models.event_division import EventDivision
from core.app_logging import logger

router = APIRouter(prefix="/api/v1/participants", tags=["participants"])


class DivisionAssignment(BaseModel):
    """Single participant division assignment"""
    participant_id: int
    division_id: Optional[int] = None
    division_name: Optional[str] = None


class BulkDivisionAssignmentRequest(BaseModel):
    """Request for bulk division assignment"""
    assignments: List[DivisionAssignment]


class BulkDivisionAssignmentResult(BaseModel):
    """Result of bulk division assignment"""
    total: int
    assigned: int
    skipped: int
    errors: List[dict]


@router.post("/bulk-assign-divisions", response_model=BulkDivisionAssignmentResult)
async def bulk_assign_divisions(
    request: BulkDivisionAssignmentRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Bulk assign divisions to multiple participants in a single transaction.
    This endpoint is optimized for auto-assignment operations to avoid rate limits.
    
    IMPORTANT: This endpoint will ONLY assign divisions to participants who have
    NO division currently assigned (division_id is NULL). Participants with existing
    division assignments will be automatically skipped to prevent overriding user choices.
    
    Requires: Event Admin or Super Admin role
    """
    # Check permissions
    if current_user.role not in ["super_admin", "event_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    result = BulkDivisionAssignmentResult(
        total=len(request.assignments),
        assigned=0,
        skipped=0,
        errors=[]
    )

    try:
        for assignment in request.assignments:
            try:
                # Get participant
                participant = session.get(Participant, assignment.participant_id)
                if not participant:
                    result.errors.append({
                        "participant_id": assignment.participant_id,
                        "error": "Participant not found"
                    })
                    result.skipped += 1
                    continue

                # SAFETY CHECK: Skip if participant already has a division assigned
                # We NEVER override existing division assignments
                if participant.division_id is not None:
                    result.skipped += 1
                    logger.info(
                        f"Skipping participant {assignment.participant_id} - "
                        f"already assigned to division {participant.division_id}"
                    )
                    continue

                # Validate division if provided
                if assignment.division_id:
                    division = session.get(EventDivision, assignment.division_id)
                    if not division:
                        result.errors.append({
                            "participant_id": assignment.participant_id,
                            "error": f"Division {assignment.division_id} not found"
                        })
                        result.skipped += 1
                        continue
                    
                    # Verify division belongs to same event
                    if division.event_id != participant.event_id:
                        result.errors.append({
                            "participant_id": assignment.participant_id,
                            "error": "Division does not belong to participant's event"
                        })
                        result.skipped += 1
                        continue
                    
                    # Check division capacity
                    if division.max_participants:
                        from sqlmodel import select, func
                        current_count = session.exec(
                            select(func.count(Participant.id))
                            .where(Participant.division_id == division.id)
                        ).one()
                        
                        if current_count >= division.max_participants:
                            result.errors.append({
                                "participant_id": assignment.participant_id,
                                "error": f"Division '{division.name}' is at maximum capacity"
                            })
                            result.skipped += 1
                            continue

                    # Update participant
                    participant.division_id = assignment.division_id
                    participant.division = assignment.division_name or division.name
                else:
                    # Clear division
                    participant.division_id = None
                    participant.division = None

                session.add(participant)
                result.assigned += 1

            except Exception as e:
                result.errors.append({
                    "participant_id": assignment.participant_id,
                    "error": str(e)
                })
                result.skipped += 1
                logger.error(f"Error assigning division for participant {assignment.participant_id}: {str(e)}")

        # Commit all changes in a single transaction
        session.commit()
        
        logger.info(
            f"Bulk division assignment completed by {current_user.email}: "
            f"{result.assigned} assigned, {result.skipped} skipped, "
            f"{len(result.errors)} errors"
        )

    except Exception as e:
        session.rollback()
        logger.error(f"Error during bulk division assignment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assign divisions: {str(e)}"
        )

    return result

