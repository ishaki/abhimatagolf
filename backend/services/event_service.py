from sqlmodel import Session, select, func
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from models.event import Event, ScoringType
from models.course import Course
from models.user import User
from models.participant import Participant
from schemas.event import EventCreate, EventUpdate, EventResponse, EventStats


class EventService:
    def __init__(self, session: Session):
        self.session = session

    def create_event(self, event_data: EventCreate, created_by: int) -> Event:
        """Create a new event"""
        event = Event(
            name=event_data.name,
            description=event_data.description,
            event_date=event_data.event_date,
            course_id=event_data.course_id,
            created_by=created_by,
            scoring_type=event_data.scoring_type,
            is_active=event_data.is_active
        )
        self.session.add(event)
        self.session.commit()
        self.session.refresh(event)
        return event

    def get_event(self, event_id: int) -> Optional[Event]:
        """Get event by ID"""
        statement = select(Event).where(Event.id == event_id)
        return self.session.exec(statement).first()

    def get_events(
        self, 
        page: int = 1, 
        per_page: int = 10, 
        search: Optional[str] = None,
        course_id: Optional[int] = None,
        scoring_type: Optional[ScoringType] = None,
        is_active: Optional[bool] = None,
        created_by: Optional[int] = None
    ) -> tuple[List[Event], int]:
        """Get events with filtering and pagination"""
        # Build query
        statement = select(Event)
        count_statement = select(func.count(Event.id))
        
        # Apply filters
        if search:
            search_filter = f"%{search}%"
            statement = statement.where(Event.name.ilike(search_filter))
            count_statement = count_statement.where(Event.name.ilike(search_filter))
        
        if course_id:
            statement = statement.where(Event.course_id == course_id)
            count_statement = count_statement.where(Event.course_id == course_id)
        
        if scoring_type:
            statement = statement.where(Event.scoring_type == scoring_type)
            count_statement = count_statement.where(Event.scoring_type == scoring_type)
        
        if is_active is not None:
            statement = statement.where(Event.is_active == is_active)
            count_statement = count_statement.where(Event.is_active == is_active)
        
        if created_by:
            statement = statement.where(Event.created_by == created_by)
            count_statement = count_statement.where(Event.created_by == created_by)
        
        # Apply pagination
        offset = (page - 1) * per_page
        statement = statement.offset(offset).limit(per_page)
        
        # Order by event date descending
        statement = statement.order_by(Event.event_date.desc())
        
        # Execute queries
        events = self.session.exec(statement).all()
        total = self.session.exec(count_statement).one()
        
        return events, total

    def update_event(self, event_id: int, event_data: EventUpdate) -> Optional[Event]:
        """Update event"""
        event = self.get_event(event_id)
        if not event:
            return None
        
        # Update fields
        update_data = event_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(event, field, value)
        
        event.updated_at = datetime.utcnow()
        self.session.add(event)
        self.session.commit()
        self.session.refresh(event)
        return event

    def delete_event(self, event_id: int) -> bool:
        """Delete event"""
        event = self.get_event(event_id)
        if not event:
            return False
        
        self.session.delete(event)
        self.session.commit()
        return True

    def get_event_with_details(self, event_id: int) -> Optional[EventResponse]:
        """Get event with related data"""
        statement = select(Event).where(Event.id == event_id)
        event = self.session.exec(statement).first()
        
        if not event:
            return None
        
        # Get related data
        course_statement = select(Course).where(Course.id == event.course_id)
        course = self.session.exec(course_statement).first()
        
        creator_statement = select(User).where(User.id == event.created_by)
        creator = self.session.exec(creator_statement).first()
        
        participant_count_statement = select(func.count(Participant.id)).where(Participant.event_id == event_id)
        participant_count = self.session.exec(participant_count_statement).one()
        
        return EventResponse(
            id=event.id,
            name=event.name,
            event_date=event.event_date,
            course_id=event.course_id,
            created_by=event.created_by,
            scoring_type=event.scoring_type,
            divisions_config=event.divisions_config,
            is_active=event.is_active,
            created_at=event.created_at,
            updated_at=event.updated_at,
            course_name=course.name if course else None,
            creator_name=creator.full_name if creator else None,
            participant_count=participant_count
        )

    def get_event_stats(self) -> EventStats:
        """Get event statistics"""
        total_events = self.session.exec(select(func.count(Event.id))).one()
        active_events = self.session.exec(select(func.count(Event.id)).where(Event.is_active == True)).one()
        
        today = date.today()
        upcoming_events = self.session.exec(
            select(func.count(Event.id)).where(Event.event_date >= today)
        ).one()
        
        completed_events = self.session.exec(
            select(func.count(Event.id)).where(Event.event_date < today)
        ).one()
        
        return EventStats(
            total_events=total_events,
            active_events=active_events,
            upcoming_events=upcoming_events,
            completed_events=completed_events
        )

    def duplicate_event(self, event_id: int, new_name: str, new_date: date) -> Optional[Event]:
        """Duplicate an existing event"""
        original_event = self.get_event(event_id)
        if not original_event:
            return None
        
        # Create new event with same settings
        new_event = Event(
            name=new_name,
            event_date=new_date,
            course_id=original_event.course_id,
            created_by=original_event.created_by,
            scoring_type=original_event.scoring_type,
            divisions_config=original_event.divisions_config,
            is_active=True
        )
        
        self.session.add(new_event)
        self.session.commit()
        self.session.refresh(new_event)
        return new_event
