from typing import Dict, List, Optional, Any, Set
from datetime import datetime
import asyncio
from sqlmodel import Session
from models.event import Event
from models.participant import Participant
from models.scorecard import Scorecard
from schemas.leaderboard import LeaderboardResponse
from services.leaderboard_service import LeaderboardService
from core.app_logging import logger
from core.websocket_manager import connection_manager


class LiveScoringService:
    """Service for live scoring updates via native WebSocket"""

    def __init__(self, session: Session):
        self.session = session
        self.leaderboard_service = LeaderboardService(session)
        
        # PERFORMANCE OPTIMIZATION: Debounced leaderboard updates
        self._events_needing_leaderboard_update: Set[int] = set()
        self._leaderboard_update_task: Optional[asyncio.Task] = None
        self._debounce_delay = 5.0  # 5 seconds debounce

    # Note: WebSocket connection handling is now managed by websocket_manager.py
    # This service focuses on business logic for broadcasting updates

    async def _broadcast_leaderboard_update(self, event_id: int):
        """Broadcast updated leaderboard to all clients in event room"""
        try:
            # Invalidate cache to get fresh data
            self.leaderboard_service.invalidate_cache(event_id)
            
            # Calculate fresh leaderboard
            leaderboard = self.leaderboard_service.calculate_leaderboard(event_id, use_cache=False)
            
            # Broadcast to all clients in the event room using WebSocket manager
            await connection_manager.broadcast_leaderboard_update(event_id, leaderboard.dict())
            logger.info(f"Leaderboard update broadcasted for event {event_id}")
            
        except Exception as e:
            logger.error(f"Error broadcasting leaderboard update: {e}")

    async def broadcast_score_update(self, event_id: int, participant_id: int, hole_number: int, strokes: int):
        """Broadcast score update to all connected clients"""
        try:
            participant = self.session.get(Participant, participant_id)
            if not participant:
                logger.warning(f"Participant {participant_id} not found for score update broadcast")
                return

            # Broadcast using WebSocket manager
            await connection_manager.broadcast_score_update(
                event_id, participant_id, participant.name, hole_number, strokes
            )
            await connection_manager.broadcast_live_score_update(
                event_id, participant_id, participant.name, hole_number, strokes
            )
            
            logger.info(f"Score update broadcasted: participant {participant_id}, hole {hole_number}, strokes {strokes}")

            # PERFORMANCE OPTIMIZATION: Schedule debounced leaderboard update
            # This eliminates ~1000ms blocking operation
            self._schedule_leaderboard_update(event_id)

        except Exception as e:
            logger.error(f"Error broadcasting score update: {e}")

    async def broadcast_leaderboard_update(self, event_id: int):
        """Broadcast leaderboard update to all connected clients"""
        await self._broadcast_leaderboard_update(event_id)

    async def get_connected_clients_count(self, event_id: int) -> int:
        """Get number of connected clients for an event"""
        return connection_manager.get_connected_clients_count(event_id)

    async def broadcast_event_status_change(self, event_id: int, is_active: bool):
        """Broadcast event status change to all connected clients"""
        try:
            await connection_manager.broadcast_event_status_change(event_id, is_active)
            logger.info(f"Event status change broadcasted: event {event_id}, active: {is_active}")
            
        except Exception as e:
            logger.error(f"Error broadcasting event status change: {e}")

    async def broadcast_participant_update(self, event_id: int, participant_id: int, action: str):
        """Broadcast participant update (added, removed, updated)"""
        try:
            participant = self.session.get(Participant, participant_id)
            if not participant:
                logger.warning(f"Participant {participant_id} not found for participant update broadcast")
                return
            
            await connection_manager.broadcast_participant_update(
                event_id, participant_id, participant.name, action
            )
            logger.info(f"Participant update broadcasted: event {event_id}, participant {participant_id}, action: {action}")
            
            # Update leaderboard if participant was added/removed
            if action in ['added', 'removed']:
                await self._broadcast_leaderboard_update(event_id)
            
        except Exception as e:
            logger.error(f"Error broadcasting participant update: {e}")

    def _schedule_leaderboard_update(self, event_id: int):
        """Schedule a debounced leaderboard update for the event"""
        self._events_needing_leaderboard_update.add(event_id)
        
        # Cancel existing task if it exists
        if self._leaderboard_update_task and not self._leaderboard_update_task.done():
            self._leaderboard_update_task.cancel()
        
        # Create new task with debounce delay
        self._leaderboard_update_task = asyncio.create_task(
            self._process_leaderboard_updates()
        )

    async def _process_leaderboard_updates(self):
        """Process all pending leaderboard updates after debounce delay"""
        try:
            # Wait for debounce delay
            await asyncio.sleep(self._debounce_delay)
            
            # Process all events that need leaderboard updates
            events_to_update = self._events_needing_leaderboard_update.copy()
            self._events_needing_leaderboard_update.clear()
            
            for event_id in events_to_update:
                try:
                    await self._broadcast_leaderboard_update(event_id)
                    logger.info(f"Debounced leaderboard update completed for event {event_id}")
                except Exception as e:
                    logger.error(f"Error in debounced leaderboard update for event {event_id}: {e}")
                    
        except asyncio.CancelledError:
            logger.info("Leaderboard update task cancelled")
        except Exception as e:
            logger.error(f"Error in leaderboard update processing: {e}")
