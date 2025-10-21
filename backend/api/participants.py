from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File
from sqlmodel import Session
from typing import Optional, List
from core.database import get_session
from core.security import get_current_user
from services.participant_service import ParticipantService
from schemas.participant import (
    ParticipantCreate, ParticipantUpdate, ParticipantResponse,
    ParticipantListResponse, ParticipantBulkCreate, ParticipantStats,
    ParticipantImportRow, ParticipantImportResult
)
from models.user import User
from core.app_logging import logger
import pandas as pd
import io

router = APIRouter(prefix="/api/v1/participants", tags=["participants"])


@router.get("/", response_model=ParticipantListResponse)
async def get_participants(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    event_id: Optional[int] = Query(None),
    division: Optional[str] = Query(None),
    division_id: Optional[int] = Query(None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get participants with filtering and pagination"""
    participant_service = ParticipantService(session)
    participants, total = participant_service.get_participants(
        page=page,
        per_page=per_page,
        search=search,
        event_id=event_id,
        division=division,
        division_id=division_id
    )

    # Convert to response format
    participant_responses = []
    for participant in participants:
        response = participant_service.get_participant_with_details(participant.id)
        if response:
            participant_responses.append(response)

    return ParticipantListResponse(
        participants=participant_responses,
        total=total,
        page=page,
        per_page=per_page
    )


@router.get("/{participant_id}", response_model=ParticipantResponse)
async def get_participant(
    participant_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get single participant by ID"""
    participant_service = ParticipantService(session)
    participant = participant_service.get_participant_with_details(participant_id)

    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")

    return participant


@router.post("/", response_model=ParticipantResponse, status_code=status.HTTP_201_CREATED)
async def create_participant(
    participant_data: ParticipantCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Create new participant"""
    # Check permissions
    if current_user.role not in ["super_admin", "event_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    participant_service = ParticipantService(session)

    try:
        participant = participant_service.create_participant(participant_data)
        return participant_service.get_participant_with_details(participant.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/bulk", response_model=List[ParticipantResponse], status_code=status.HTTP_201_CREATED)
async def create_participants_bulk(
    participants_data: ParticipantBulkCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Create multiple participants at once"""
    # Check permissions
    if current_user.role not in ["super_admin", "event_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    participant_service = ParticipantService(session)

    try:
        participants = participant_service.create_participants_bulk(participants_data)
        # Return with details
        return [
            participant_service.get_participant_with_details(p.id)
            for p in participants
        ]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/upload", response_model=ParticipantImportResult, status_code=status.HTTP_201_CREATED)
async def upload_participants(
    event_id: int = Query(..., description="Event ID to add participants to"),
    file: UploadFile = File(..., description="Excel or CSV file with participant data"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Upload participants from Excel or CSV file"""
    # Check permissions
    if current_user.role not in ["super_admin", "event_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    file_ext = file.filename.split('.')[-1].lower()
    if file_ext not in ['xlsx', 'xls', 'csv']:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload Excel (.xlsx, .xls) or CSV (.csv) file"
        )

    try:
        # Read file content
        contents = await file.read()

        # Parse file based on type
        if file_ext == 'csv':
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))

        # Validate required columns
        required_columns = ['name']
        optional_columns = ['declared_handicap', 'handicap', 'division', 'division_id']

        if 'name' not in df.columns:
            raise HTTPException(
                status_code=400,
                detail="Excel/CSV file must have a 'name' column"
            )

        # Normalize column names
        df.columns = df.columns.str.lower().str.strip()

        # Handle handicap column variations
        if 'handicap' in df.columns and 'declared_handicap' not in df.columns:
            df['declared_handicap'] = df['handicap']

        # Fill missing values
        df['declared_handicap'] = df.get('declared_handicap', 0).fillna(0)
        df['division'] = df.get('division', None).fillna('')
        df['division_id'] = df.get('division_id', None)
        
        # Clean division_id values - convert empty strings to None
        df['division_id'] = df['division_id'].apply(lambda x: None if pd.isna(x) or str(x).strip() == '' else x)

        # Parse rows
        participant_rows = []
        for _, row in df.iterrows():
            try:
                participant_row = ParticipantImportRow(
                    name=str(row['name']).strip(),
                    declared_handicap=float(row['declared_handicap']),
                    division=str(row['division']).strip() if row['division'] and str(row['division']).strip() else None,
                    division_id=int(row['division_id']) if row['division_id'] is not None and not pd.isna(row['division_id']) else None
                )
                participant_rows.append(participant_row)
            except Exception as e:
                logger.warning(f"Skipping invalid row: {row.to_dict()} - Error: {str(e)}")
                continue

        if not participant_rows:
            raise HTTPException(
                status_code=400,
                detail="No valid participant data found in file"
            )

        # Import participants
        participant_service = ParticipantService(session)
        created_participants, errors = participant_service.import_participants_from_list(
            event_id=event_id,
            participant_rows=participant_rows
        )

        # Get full details for created participants
        participant_responses = [
            participant_service.get_participant_with_details(p.id)
            for p in created_participants
        ]

        return ParticipantImportResult(
            success=len(errors) == 0,
            total_rows=len(participant_rows),
            successful=len(created_participants),
            failed=len(errors),
            participants=participant_responses,
            errors=errors
        )

    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="The uploaded file is empty")
    except pd.errors.ParserError as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error uploading participants: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process file: {str(e)}"
        )


@router.put("/{participant_id}", response_model=ParticipantResponse)
async def update_participant(
    participant_id: int,
    participant_data: ParticipantUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Update participant"""
    # Check permissions
    if current_user.role not in ["super_admin", "event_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    participant_service = ParticipantService(session)
    participant = participant_service.get_participant(participant_id)

    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")

    updated_participant = participant_service.update_participant(participant_id, participant_data)
    return participant_service.get_participant_with_details(participant_id)


@router.delete("/{participant_id}")
async def delete_participant(
    participant_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Delete participant"""
    # Check permissions
    if current_user.role not in ["super_admin", "event_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    participant_service = ParticipantService(session)
    participant = participant_service.get_participant(participant_id)

    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")

    success = participant_service.delete_participant(participant_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete participant"
        )

    return {"message": "Participant deleted successfully"}


@router.get("/event/{event_id}/list", response_model=List[ParticipantResponse])
async def get_event_participants(
    event_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get all participants for a specific event"""
    participant_service = ParticipantService(session)
    participants = participant_service.get_event_participants(event_id)

    return [
        participant_service.get_participant_with_details(p.id)
        for p in participants
    ]


@router.get("/event/{event_id}/stats", response_model=ParticipantStats)
async def get_participant_stats(
    event_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get participant statistics for an event"""
    participant_service = ParticipantService(session)
    return participant_service.get_participant_stats(event_id=event_id)


@router.get("/event/{event_id}/divisions", response_model=List[str])
async def get_event_divisions(
    event_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get list of divisions for an event"""
    participant_service = ParticipantService(session)
    return participant_service.get_divisions_for_event(event_id)
