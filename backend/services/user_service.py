"""
User Service Module

Provides business logic for user management, including event-specific user creation.
"""

import secrets
import string
from typing import List, Optional, Tuple
from sqlmodel import Session, select
from models.user import User, UserRole
from models.user_event import UserEvent, AccessLevel
from models.event import Event
from core.security import get_password_hash
from core.audit_logging import get_audit_logger, AuditAction


class UserService:
    """Service class for user-related operations"""
    
    def __init__(self, session: Session):
        self.session = session
        self.audit_logger = get_audit_logger()
    
    def generate_secure_password(self, length: int = 12) -> str:
        """
        Generate a secure random password.
        
        Args:
            length: Length of the password (default: 12)
            
        Returns:
            str: Generated password
        """
        # Define character sets
        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        digits = string.digits
        symbols = "!@#$%^&*"
        
        # Ensure at least one character from each set
        password = [
            secrets.choice(lowercase),
            secrets.choice(uppercase),
            secrets.choice(digits),
            secrets.choice(symbols)
        ]
        
        # Fill the rest with random characters
        all_chars = lowercase + uppercase + digits + symbols
        for _ in range(length - 4):
            password.append(secrets.choice(all_chars))
        
        # Shuffle the password
        secrets.SystemRandom().shuffle(password)
        
        return ''.join(password)
    
    def generate_event_user_email(self, event_id: int, event_name: str) -> str:
        """
        Generate a unique email for an event user.
        
        Args:
            event_id: The ID of the event
            event_name: The name of the event
            
        Returns:
            str: Generated email address
        """
        # Clean event name for email
        clean_name = ''.join(c.lower() for c in event_name if c.isalnum())[:20]
        
        # Count existing event users for this event
        existing_users_statement = select(User).where(
            User.email.like(f"event{event_id}_%")
        )
        existing_users = self.session.exec(existing_users_statement).all()
        user_count = len(existing_users) + 1
        
        return f"event{event_id}_{clean_name}_{user_count}@abhimata.local"
    
    def create_event_user(
        self,
        event_id: int,
        full_name: str,
        email: Optional[str] = None,
        password: Optional[str] = None,
        creator_user: Optional[User] = None
    ) -> Tuple[User, str, str]:
        """
        Create a new event-specific user.
        
        Args:
            event_id: The ID of the event this user will be assigned to
            full_name: The user's full name
            email: Optional email (will be auto-generated if not provided)
            password: Optional password (will be auto-generated if not provided)
            creator_user: The user creating this event user (for audit logging)
            
        Returns:
            Tuple[User, str, str]: (created_user, email, password)
            
        Raises:
            ValueError: If event doesn't exist or user creation fails
        """
        # Verify event exists
        event_statement = select(Event).where(Event.id == event_id)
        event = self.session.exec(event_statement).first()
        if not event:
            raise ValueError(f"Event with ID {event_id} not found")
        
        # Generate email if not provided
        if not email:
            email = self.generate_event_user_email(event_id, event.name)
        
        # Check if email already exists
        existing_user_statement = select(User).where(User.email == email)
        existing_user = self.session.exec(existing_user_statement).first()
        if existing_user:
            raise ValueError(f"Email {email} already exists")
        
        # Generate password if not provided
        if not password:
            password = self.generate_secure_password()
        
        # Create user
        hashed_password = get_password_hash(password)
        user = User(
            full_name=full_name,
            email=email,
            hashed_password=hashed_password,
            role=UserRole.EVENT_USER,
            is_active=True
        )
        
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        
        # Create user-event relationship
        user_event = UserEvent(
            user_id=user.id,
            event_id=event_id,
            access_level=AccessLevel.READ_WRITE
        )
        
        self.session.add(user_event)
        self.session.commit()
        
        # Log the creation
        if creator_user:
            self.audit_logger.log_user_action(
                action=AuditAction.USER_CREATE,
                user_id=creator_user.id,
                user_email=creator_user.email,
                user_role=creator_user.role,
                resource_type="user",
                description=f"Created event user '{full_name}' for event '{event.name}'",
                resource_id=user.id
            )
        
        return user, email, password
    
    def get_event_users(self, event_id: int) -> List[Tuple[User, UserEvent]]:
        """
        Get all users associated with a specific event.
        
        Args:
            event_id: The ID of the event
            
        Returns:
            List[Tuple[User, UserEvent]]: List of (user, user_event) tuples
        """
        statement = select(User, UserEvent).join(UserEvent).where(
            UserEvent.event_id == event_id
        )
        results = self.session.exec(statement).all()
        return results
    
    def get_user_events(self, user_id: int) -> List[Tuple[Event, UserEvent]]:
        """
        Get all events associated with a specific user.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            List[Tuple[Event, UserEvent]]: List of (event, user_event) tuples
        """
        statement = select(Event, UserEvent).join(UserEvent).where(
            UserEvent.user_id == user_id
        )
        results = self.session.exec(statement).all()
        return results
    
    def remove_user_from_event(self, user_id: int, event_id: int, creator_user: Optional[User] = None) -> bool:
        """
        Remove a user from an event (delete UserEvent relationship).
        
        Args:
            user_id: The ID of the user
            event_id: The ID of the event
            creator_user: The user performing this action (for audit logging)
            
        Returns:
            bool: True if successful, False if relationship didn't exist
        """
        user_event_statement = select(UserEvent).where(
            UserEvent.user_id == user_id,
            UserEvent.event_id == event_id
        )
        user_event = self.session.exec(user_event_statement).first()
        
        if not user_event:
            return False
        
        # Get user and event info for logging
        user_statement = select(User).where(User.id == user_id)
        user = self.session.exec(user_statement).first()
        
        event_statement = select(Event).where(Event.id == event_id)
        event = self.session.exec(event_statement).first()
        
        # Delete the relationship
        self.session.delete(user_event)
        self.session.commit()
        
        # Log the removal
        if creator_user and user and event:
            self.audit_logger.log_user_action(
                action=AuditAction.USER_DELETE,
                user_id=creator_user.id,
                user_email=creator_user.email,
                user_role=creator_user.role,
                resource_type="user_event",
                description=f"Removed user '{user.full_name}' from event '{event.name}'",
                resource_id=user_event.id
            )
        
        return True
    
    def deactivate_event_user(self, user_id: int, creator_user: Optional[User] = None) -> bool:
        """
        Deactivate an event user (set is_active=False).
        
        Args:
            user_id: The ID of the user to deactivate
            creator_user: The user performing this action (for audit logging)
            
        Returns:
            bool: True if successful, False if user not found
        """
        user_statement = select(User).where(User.id == user_id)
        user = self.session.exec(user_statement).first()
        
        if not user:
            return False
        
        # Only allow deactivating EVENT_USER role
        if user.role != UserRole.EVENT_USER:
            raise ValueError("Can only deactivate event users")
        
        user.is_active = False
        self.session.add(user)
        self.session.commit()
        
        # Log the deactivation
        if creator_user:
            self.audit_logger.log_user_action(
                action=AuditAction.USER_UPDATE,
                user_id=creator_user.id,
                user_email=creator_user.email,
                user_role=creator_user.role,
                resource_type="user",
                description=f"Deactivated event user '{user.full_name}'",
                resource_id=user.id
            )
        
        return True


def create_user_service(session: Session) -> UserService:
    """Factory function to create a UserService instance"""
    return UserService(session)