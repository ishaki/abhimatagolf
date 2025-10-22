"""
Permission System Module

Provides role-based access control (RBAC) and event-specific access control
for the Abhimata Golf application.
"""

from typing import List, Optional
from fastapi import Depends, HTTPException, status
from sqlmodel import Session, select
from core.database import get_session
from models.user import User, UserRole
from models.user_event import UserEvent, AccessLevel
from models.event import Event
from api.auth import get_current_user


class PermissionError(Exception):
    """Custom exception for permission-related errors"""
    pass


def require_role(allowed_roles: List[UserRole]):
    """
    Dependency function to require specific roles for route access.
    
    Args:
        allowed_roles: List of UserRole enums that are allowed to access the route
        
    Returns:
        User: The authenticated user if they have the required role
        
    Raises:
        HTTPException: If user doesn't have required role
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {[role.value for role in allowed_roles]}"
            )
        return current_user
    
    return role_checker


def require_super_admin():
    """Dependency to require SUPER_ADMIN role"""
    return require_role([UserRole.SUPER_ADMIN])


def require_event_admin_or_super():
    """Dependency to require EVENT_ADMIN or SUPER_ADMIN role"""
    return require_role([UserRole.EVENT_ADMIN, UserRole.SUPER_ADMIN])


def require_event_access(event_id: int):
    """
    Dependency to require access to a specific event.
    
    Args:
        event_id: The ID of the event to check access for
        
    Returns:
        User: The authenticated user if they have access to the event
        
    Raises:
        HTTPException: If user doesn't have access to the event
    """
    def event_access_checker(
        current_user: User = Depends(get_current_user),
        session: Session = Depends(get_session)
    ) -> User:
        if not can_access_event(current_user, event_id, session):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this event"
            )
        return current_user
    
    return event_access_checker


def can_access_event(user: User, event_id: int, session: Session) -> bool:
    """
    Check if a user can access a specific event.
    
    Args:
        user: The user to check
        event_id: The ID of the event
        session: Database session
        
    Returns:
        bool: True if user can access the event, False otherwise
    """
    # Super admins can access all events
    if user.role == UserRole.SUPER_ADMIN:
        return True
    
    # Event admins can access events they created
    if user.role == UserRole.EVENT_ADMIN:
        event_statement = select(Event).where(Event.id == event_id)
        event = session.exec(event_statement).first()
        if event and event.created_by == user.id:
            return True
    
    # Event users can access events they're assigned to
    if user.role == UserRole.EVENT_USER:
        user_event_statement = select(UserEvent).where(
            UserEvent.user_id == user.id,
            UserEvent.event_id == event_id
        )
        user_event = session.exec(user_event_statement).first()
        if user_event:
            return True
    
    return False


def can_manage_courses(user: User) -> bool:
    """
    Check if user can manage (create/edit/delete) courses.
    
    Args:
        user: The user to check
        
    Returns:
        bool: True if user can manage courses, False otherwise
    """
    return user.role == UserRole.SUPER_ADMIN


def can_manage_users(user: User) -> bool:
    """
    Check if user can manage (create/edit/delete) users.
    
    Args:
        user: The user to check
        
    Returns:
        bool: True if user can manage users, False otherwise
    """
    return user.role == UserRole.SUPER_ADMIN


def can_create_event_users(user: User) -> bool:
    """
    Check if user can create event-specific users.
    
    Args:
        user: The user to check
        
    Returns:
        bool: True if user can create event users, False otherwise
    """
    return user.role in [UserRole.EVENT_ADMIN, UserRole.SUPER_ADMIN]


def can_access_winners(user: User) -> bool:
    """
    Check if user can access winner calculation and management.
    
    Args:
        user: The user to check
        
    Returns:
        bool: True if user can access winners, False otherwise
    """
    return user.role in [UserRole.EVENT_ADMIN, UserRole.SUPER_ADMIN]


def can_view_winners(user: User) -> bool:
    """
    Check if user can view winner results (read-only).
    
    Args:
        user: The user to check
        
    Returns:
        bool: True if user can view winners, False otherwise
    """
    return user.role in [UserRole.EVENT_ADMIN, UserRole.SUPER_ADMIN]


def can_manage_scores(user: User, event_id: int, session: Session) -> bool:
    """
    Check if user can manage scores for a specific event.
    
    Args:
        user: The user to check
        event_id: The ID of the event
        session: Database session
        
    Returns:
        bool: True if user can manage scores for the event, False otherwise
    """
    if user.role == UserRole.SUPER_ADMIN:
        return True
    
    elif user.role == UserRole.EVENT_ADMIN:
        # Event admins can manage scores for events they created
        event = session.get(Event, event_id)
        return event and event.created_by == user.id
    
    elif user.role == UserRole.EVENT_USER:
        # Event users can manage scores for events they're assigned to
        user_event_statement = select(UserEvent).where(
            UserEvent.user_id == user.id,
            UserEvent.event_id == event_id
        )
        user_event = session.exec(user_event_statement).first()
        return user_event is not None
    
    return False


def get_user_accessible_events(user: User, session: Session) -> List[int]:
    """
    Get list of event IDs that a user can access.
    
    Args:
        user: The user to check
        session: Database session
        
    Returns:
        List[int]: List of event IDs the user can access
    """
    if user.role == UserRole.SUPER_ADMIN:
        # Super admins can access all events
        events_statement = select(Event.id)
        events = session.exec(events_statement).all()
        return list(events)
    
    elif user.role == UserRole.EVENT_ADMIN:
        # Event admins can access events they created
        events_statement = select(Event.id).where(Event.created_by == user.id)
        events = session.exec(events_statement).all()
        return list(events)
    
    elif user.role == UserRole.EVENT_USER:
        # Event users can access events they're assigned to
        user_events_statement = select(UserEvent.event_id).where(UserEvent.user_id == user.id)
        user_events = session.exec(user_events_statement).all()
        return list(user_events)
    
    return []


def check_event_ownership(user: User, event_id: int, session: Session) -> bool:
    """
    Check if user owns/created a specific event.
    
    Args:
        user: The user to check
        event_id: The ID of the event
        session: Database session
        
    Returns:
        bool: True if user owns the event, False otherwise
    """
    if user.role == UserRole.SUPER_ADMIN:
        return True
    
    event_statement = select(Event).where(Event.id == event_id)
    event = session.exec(event_statement).first()
    
    return event and event.created_by == user.id


def get_user_event_access_level(user: User, event_id: int, session: Session) -> Optional[AccessLevel]:
    """
    Get the access level a user has for a specific event.
    
    Args:
        user: The user to check
        event_id: The ID of the event
        session: Database session
        
    Returns:
        Optional[AccessLevel]: The access level or None if no access
    """
    if user.role == UserRole.SUPER_ADMIN:
        return AccessLevel.ADMIN
    
    if user.role == UserRole.EVENT_ADMIN:
        if check_event_ownership(user, event_id, session):
            return AccessLevel.ADMIN
    
    if user.role == UserRole.EVENT_USER:
        user_event_statement = select(UserEvent).where(
            UserEvent.user_id == user.id,
            UserEvent.event_id == event_id
        )
        user_event = session.exec(user_event_statement).first()
        if user_event:
            return user_event.access_level
    
    return None
