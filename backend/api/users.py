from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlmodel import Session, select, func
from typing import List, Optional
from pydantic import BaseModel
from core.database import get_session
from core.security import get_password_hash
from core.audit_logging import get_audit_logger, AuditAction
from core.error_handling import create_secure_http_exception, ErrorCode, raise_security_error
from core.permissions import require_event_admin_or_super, require_super_admin, require_event_access, can_create_event_users
from models.user import User, UserRole
from models.user_event import UserEvent
from schemas.user import UserCreate, UserUpdate, UserResponse, UserListResponse
from api.auth import get_current_user
from services.user_service import UserService, create_user_service

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@router.get("/", response_model=UserListResponse)
async def get_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    """Get list of users with pagination and search"""
    
    audit_logger = get_audit_logger()
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    # Check permissions (only super_admin can view all users)
    if current_user.role != UserRole.SUPER_ADMIN:
        audit_logger.log_permission_denied(
            user_id=current_user.id,
            user_email=current_user.email,
            user_role=current_user.role,
            attempted_action="view_all_users",
            resource_type="user",
            ip_address=client_ip,
            user_agent=user_agent
        )
        raise create_secure_http_exception(
            status_code=status.HTTP_403_FORBIDDEN,
            message="Insufficient permissions to access this resource",
            error_code=ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS,
            details={"required_role": "SUPER_ADMIN", "current_role": current_user.role}
        )
    
    # Build query
    statement = select(User)

    if search:
        statement = statement.where(
            User.full_name.contains(search) | User.email.contains(search)
        )

    # Get total count
    count_statement = select(func.count(User.id))
    if search:
        count_statement = count_statement.where(
            User.full_name.contains(search) | User.email.contains(search)
        )
    
    total = session.exec(count_statement).one()
    
    # Apply pagination
    offset = (page - 1) * per_page
    statement = statement.offset(offset).limit(per_page)
    
    users = session.exec(statement).all()

    # Log user list access
    audit_logger.log_user_action(
        action=AuditAction.USER_CREATE,  # Using as generic user action
        user_id=current_user.id,
        user_email=current_user.email,
        user_role=current_user.role,
        resource_type="user",
        description=f"Viewed user list (page {page}, total {total})",
        ip_address=client_ip,
        user_agent=user_agent
    )

    return UserListResponse(
        users=[UserResponse.model_validate(user, from_attributes=True) for user in users],
        total=total,
        page=page,
        per_page=per_page
    )


@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_super_admin())
):
    """Create a new user - SUPER_ADMIN only"""
    
    # Check if email already exists
    statement = select(User).where(User.email == user_data.email)
    existing_user = session.exec(statement).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        full_name=user_data.full_name,
        email=user_data.email,
        hashed_password=hashed_password,
        role=user_data.role,
        is_active=user_data.is_active
    )

    session.add(user)
    session.commit()
    session.refresh(user)

    return UserResponse.model_validate(user, from_attributes=True)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get user by ID"""
    
    # Check permissions
    if current_user.role != UserRole.SUPER_ADMIN and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    statement = select(User).where(User.id == user_id)
    user = session.exec(statement).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.model_validate(user, from_attributes=True)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_super_admin())
):
    """Update a user - SUPER_ADMIN only"""
    
    statement = select(User).where(User.id == user_id)
    user = session.exec(statement).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields
    update_data = user_data.model_dump(exclude_unset=True)
    
    # Check email uniqueness if updating email
    if "email" in update_data:
        email_statement = select(User).where(User.email == update_data["email"])
        existing_user = session.exec(email_statement).first()
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return UserResponse.model_validate(user, from_attributes=True)


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_super_admin())
):
    """Delete a user - SUPER_ADMIN only"""
    
    # Prevent self-deletion
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    statement = select(User).where(User.id == user_id)
    user = session.exec(statement).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    session.delete(user)
    session.commit()
    
    return {"message": "User deleted successfully"}


# Event User Creation Schemas
class EventUserCreate(BaseModel):
    full_name: str
    email: Optional[str] = None
    password: Optional[str] = None


class EventUserCreateResponse(BaseModel):
    user: UserResponse
    email: str
    password: str
    message: str


class EventUserResponse(BaseModel):
    user: UserResponse
    access_level: str
    assigned_at: str


class EventUsersListResponse(BaseModel):
    users: List[EventUserResponse]
    total: int


@router.post("/event/{event_id}/create", response_model=EventUserCreateResponse)
async def create_event_user(
    event_id: int,
    user_data: EventUserCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_event_admin_or_super())
):
    """Create a new event-specific user"""
    
    # Check if user can create event users
    if not can_create_event_users(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create event users"
        )
    
    # Check if current user has access to the event
    from core.permissions import can_access_event
    if not can_access_event(current_user, event_id, session):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this event"
        )
    
    try:
        # Create user service
        user_service = create_user_service(session)
        
        # Create the event user
        user, email, password = user_service.create_event_user(
            event_id=event_id,
            full_name=user_data.full_name,
            email=user_data.email,
            password=user_data.password,
            creator_user=current_user
        )
        
        return EventUserCreateResponse(
            user=UserResponse.model_validate(user, from_attributes=True),
            email=email,
            password=password,
            message="Event user created successfully. Save these credentials - they won't be shown again."
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create event user"
        )


@router.get("/event/{event_id}", response_model=EventUsersListResponse)
async def get_event_users(
    event_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_event_admin_or_super())
):
    """Get all users associated with a specific event"""
    
    # Check if current user has access to the event
    from core.permissions import can_access_event
    if not can_access_event(current_user, event_id, session):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this event"
        )
    
    try:
        # Create user service
        user_service = create_user_service(session)
        
        # Get event users
        event_users = user_service.get_event_users(event_id)
        
        # Format response
        users_response = []
        for user, user_event in event_users:
            users_response.append(EventUserResponse(
                user=UserResponse.model_validate(user, from_attributes=True),
                access_level=user_event.access_level.value,
                assigned_at=user_event.assigned_at.isoformat()
            ))
        
        return EventUsersListResponse(
            users=users_response,
            total=len(users_response)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get event users"
        )


@router.put("/event/{event_id}/user/{user_id}/access")
async def update_user_event_access(
    event_id: int,
    user_id: int,
    access_data: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_super_admin())
):
    """Update a user's access level for an event - SUPER_ADMIN only"""
    
    # Check if current user has access to the event
    from core.permissions import can_access_event
    if not can_access_event(current_user, event_id, session):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this event"
        )
    
    # Validate access level
    from models.user_event import AccessLevel
    access_level = access_data.get('access_level')
    if access_level not in [level.value for level in AccessLevel]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid access level. Must be one of: {[level.value for level in AccessLevel]}"
        )
    
    try:
        # Create user service
        user_service = create_user_service(session)
        
        # Update user access level
        success = user_service.update_user_event_access(
            user_id=user_id,
            event_id=event_id,
            access_level=AccessLevel(access_level),
            updater_user=current_user
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found in this event"
            )
        
        return {"message": f"User access level updated to {access_level} successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user access level"
        )


@router.delete("/event/{event_id}/user/{user_id}")
async def remove_user_from_event(
    event_id: int,
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_event_admin_or_super())
):
    """Remove a user from an event"""
    
    # Check if current user has access to the event
    from core.permissions import can_access_event
    if not can_access_event(current_user, event_id, session):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this event"
        )
    
    try:
        # Create user service
        user_service = create_user_service(session)
        
        # Remove user from event
        success = user_service.remove_user_from_event(
            user_id=user_id,
            event_id=event_id,
            creator_user=current_user
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found in this event"
            )
        
        return {"message": "User removed from event successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove user from event"
        )
