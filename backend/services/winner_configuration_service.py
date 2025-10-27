"""
Winner Configuration Service

Service for managing winner calculation configuration per event
"""

from typing import Optional
from sqlmodel import Session, select
from datetime import datetime

from models.winner_configuration import WinnerConfiguration, TieBreakingMethod, CalculationTrigger
from models.event import Event
from schemas.winner_configuration import (
    WinnerConfigurationCreate,
    WinnerConfigurationUpdate
)
from core.app_logging import logger


class WinnerConfigurationService:
    """Service for winner configuration CRUD operations"""

    @staticmethod
    def get_config_by_event(session: Session, event_id: int) -> Optional[WinnerConfiguration]:
        """
        Get winner configuration for an event

        Args:
            session: Database session
            event_id: Event ID

        Returns:
            WinnerConfiguration or None if not found
        """
        statement = select(WinnerConfiguration).where(WinnerConfiguration.event_id == event_id)
        return session.exec(statement).first()

    @staticmethod
    def create_config(
        session: Session,
        config_data: WinnerConfigurationCreate,
        user_id: int
    ) -> WinnerConfiguration:
        """
        Create winner configuration for an event

        Args:
            session: Database session
            config_data: Configuration data
            user_id: User creating the configuration

        Returns:
            Created WinnerConfiguration

        Raises:
            ValueError: If event not found or configuration already exists
        """
        # Verify event exists
        event = session.get(Event, config_data.event_id)
        if not event:
            raise ValueError(f"Event {config_data.event_id} not found")

        # Check if configuration already exists
        existing_config = WinnerConfigurationService.get_config_by_event(session, config_data.event_id)
        if existing_config:
            raise ValueError(f"Winner configuration already exists for event {config_data.event_id}")

        # Create configuration
        config = WinnerConfiguration(
            event_id=config_data.event_id,
            tie_breaking_method=config_data.tie_breaking_method,
            award_categories=config_data.award_categories,
            winners_per_division=config_data.winners_per_division,
            top_overall_count=config_data.top_overall_count,
            calculation_trigger=config_data.calculation_trigger,
            allow_manual_override=config_data.allow_manual_override,
            include_best_gross=config_data.include_best_gross,
            include_best_net=config_data.include_best_net,
            exclude_incomplete_rounds=config_data.exclude_incomplete_rounds,
            minimum_holes_for_ranking=config_data.minimum_holes_for_ranking,
            created_by=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        session.add(config)
        session.commit()
        session.refresh(config)

        logger.info(f"Created winner configuration for event {config_data.event_id} by user {user_id}")
        return config

    @staticmethod
    def update_config(
        session: Session,
        event_id: int,
        config_update: WinnerConfigurationUpdate
    ) -> Optional[WinnerConfiguration]:
        """
        Update winner configuration for an event

        Args:
            session: Database session
            event_id: Event ID
            config_update: Updated configuration data

        Returns:
            Updated WinnerConfiguration or None if not found
        """
        config = WinnerConfigurationService.get_config_by_event(session, event_id)
        if not config:
            return None

        # Update fields if provided
        update_data = config_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(config, key, value)

        config.updated_at = datetime.utcnow()

        session.add(config)
        session.commit()
        session.refresh(config)

        logger.info(f"Updated winner configuration for event {event_id}")
        return config

    @staticmethod
    def delete_config(session: Session, event_id: int) -> bool:
        """
        Delete winner configuration for an event

        Args:
            session: Database session
            event_id: Event ID

        Returns:
            True if deleted, False if not found
        """
        config = WinnerConfigurationService.get_config_by_event(session, event_id)
        if not config:
            return False

        session.delete(config)
        session.commit()

        logger.info(f"Deleted winner configuration for event {event_id}")
        return True

    @staticmethod
    def create_default_config(
        session: Session,
        event_id: int,
        user_id: int
    ) -> WinnerConfiguration:
        """
        Create default winner configuration for an event

        Args:
            session: Database session
            event_id: Event ID
            user_id: User creating the configuration

        Returns:
            Created WinnerConfiguration with default values
        """
        config_data = WinnerConfigurationCreate(event_id=event_id)
        return WinnerConfigurationService.create_config(session, config_data, user_id)

    @staticmethod
    def get_or_create_config(
        session: Session,
        event_id: int,
        user_id: int
    ) -> WinnerConfiguration:
        """
        Get existing configuration or create default if not exists

        Args:
            session: Database session
            event_id: Event ID
            user_id: User ID for creating default config

        Returns:
            WinnerConfiguration (existing or newly created)
        """
        config = WinnerConfigurationService.get_config_by_event(session, event_id)
        if not config:
            logger.info(f"No winner configuration found for event {event_id}, creating default")
            config = WinnerConfigurationService.create_default_config(session, event_id, user_id)
        return config
