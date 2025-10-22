from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlmodel import Session
from typing import Optional
from datetime import datetime
from core.database import get_session
from core.security import get_current_user
from models.user import User
from services.excel_service import ExcelService
from core.app_logging import logger

router = APIRouter(prefix="/api/v1/excel", tags=["Excel Export"])


@router.get("/participants/event/{event_id}/export")
async def export_participants_to_excel(
    event_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Export participants for an event to Excel format.
    Requires authentication.
    """
    try:
        excel_service = ExcelService(session)
        excel_file = excel_service.export_participants_to_excel(event_id)
        
        # Generate filename
        filename = f"participants_event_{event_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return StreamingResponse(
            excel_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error exporting participants to Excel: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export participants: {str(e)}"
        )


@router.get("/scorecards/event/{event_id}/export")
async def export_scorecards_to_excel(
    event_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Export scorecards for an event to Excel format.
    Requires authentication.
    """
    try:
        excel_service = ExcelService(session)
        excel_file = excel_service.export_scorecards_to_excel(event_id)
        
        # Generate filename
        filename = f"scorecards_event_{event_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return StreamingResponse(
            excel_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error exporting scorecards to Excel: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export scorecards: {str(e)}"
        )


@router.get("/template/participants")
async def download_participant_template(
    event_id: Optional[int] = Query(None, description="Event ID to include division list in template"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Download Excel template for participant upload.
    Optionally provide event_id to include event divisions reference.
    Requires authentication.
    """
    try:
        excel_service = ExcelService(session)
        excel_file = excel_service.generate_participant_template(event_id=event_id)
        
        # Generate filename
        filename = f"participant_upload_template_{datetime.now().strftime('%Y%m%d')}.xlsx"
        
        return StreamingResponse(
            excel_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Error generating participant template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate template: {str(e)}"
        )
