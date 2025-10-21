import socketio
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


class LiveScoringService:
    """Service for live scoring updates via WebSocket"""

    def __init__(self, session: Session):
        self.session = session
        self.sio = socketio.AsyncServer(
            cors_allowed_origins="*",
            logger=True,
            engineio_logger=True
        )
        self.leaderboard_service = LeaderboardService(session)
        
        # PERFORMANCE OPTIMIZATION: Debounced leaderboard updates
        self._events_needing_leaderboard_update: Set[int] = set()
        self._leaderboard_update_task: Optional[asyncio.Task] = None
        self._debounce_delay = 5.0  # 5 seconds debounce
        
        self._setup_handlers()

    def _setup_handlers(self):
        """Setup WebSocket event handlers"""
        
        @self.sio.event
        async def connect(sid, environ, auth):
            """Handle client connection"""
            logger.info(f"Client {sid} connected")
            await self.sio.emit('connected', {'message': 'Connected to live scoring'}, room=sid)

        @self.sio.event
        async def disconnect(sid):
            """Handle client disconnection"""
            logger.info(f"Client {sid} disconnected")

        @self.sio.event
        async def join_event(sid, data):
            """Join a specific event room for live updates"""
            event_id = data.get('event_id')
            if not event_id:
                await self.sio.emit('error', {'message': 'Event ID required'}, room=sid)
                return
            
            # Validate event exists
            event = self.session.get(Event, event_id)
            if not event:
                await self.sio.emit('error', {'message': 'Event not found'}, room=sid)
                return
            
            # Join the event room
            self.sio.enter_room(sid, f'event_{event_id}')
            logger.info(f"Client {sid} joined event {event_id}")
            
            # Send current leaderboard
            try:
                leaderboard = self.leaderboard_service.calculate_leaderboard(event_id, use_cache=False)
                await self.sio.emit('leaderboard_update', leaderboard.dict(), room=sid)
            except Exception as e:
                logger.error(f"Error sending initial leaderboard: {e}")
                await self.sio.emit('error', {'message': 'Failed to load leaderboard'}, room=sid)

        @self.sio.event
        async def leave_event(sid, data):
            """Leave an event room"""
            event_id = data.get('event_id')
            if event_id:
                self.sio.leave_room(sid, f'event_{event_id}')
                logger.info(f"Client {sid} left event {event_id}")

        @self.sio.event
        async def score_update(sid, data):
            """Handle score update from client"""
            try:
                participant_id = data.get('participant_id')
                hole_number = data.get('hole_number')
                strokes = data.get('strokes')
                
                if not all([participant_id, hole_number, strokes]):
                    await self.sio.emit('error', {'message': 'Missing required fields'}, room=sid)
                    return
                
                # Validate participant
                participant = self.session.get(Participant, participant_id)
                if not participant:
                    await self.sio.emit('error', {'message': 'Participant not found'}, room=sid)
                    return
                
                # Get event
                event = self.session.get(Event, participant.event_id)
                if not event:
                    await self.sio.emit('error', {'message': 'Event not found'}, room=sid)
                    return
                
                # Broadcast score update to all clients in the event room
                score_data = {
                    'participant_id': participant_id,
                    'participant_name': participant.name,
                    'hole_number': hole_number,
                    'strokes': strokes,
                    'timestamp': datetime.utcnow().isoformat(),
                    'event_id': event.id
                }
                
                await self.sio.emit('score_updated', score_data, room=f'event_{event.id}')
                logger.info(f"Score update broadcasted: {score_data}")
                
                # PERFORMANCE OPTIMIZATION: Remove synchronous leaderboard recalculation
                # Clients can poll leaderboard separately or use auto-refresh
                # This eliminates ~1000ms blocking operation
                
            except Exception as e:
                logger.error(f"Error handling score update: {e}")
                await self.sio.emit('error', {'message': 'Failed to process score update'}, room=sid)

    async def _broadcast_leaderboard_update(self, event_id: int):
        """Broadcast updated leaderboard to all clients in event room"""
        try:
            # Invalidate cache to get fresh data
            self.leaderboard_service.invalidate_cache(event_id)
            
            # Calculate fresh leaderboard
            leaderboard = self.leaderboard_service.calculate_leaderboard(event_id, use_cache=False)
            
            # Broadcast to all clients in the event room
            await self.sio.emit('leaderboard_update', leaderboard.dict(), room=f'event_{event_id}')
            logger.info(f"Leaderboard update broadcasted for event {event_id}")
            
        except Exception as e:
            logger.error(f"Error broadcasting leaderboard update: {e}")

    async def broadcast_score_update(self, event_id: int, participant_id: int, hole_number: int, strokes: int):
        """Broadcast score update to all connected clients"""
        try:
            participant = self.session.get(Participant, participant_id)
            if not participant:
                return

            score_data = {
                'participant_id': participant_id,
                'participant_name': participant.name,
                'hole_number': hole_number,
                'strokes': strokes,
                'timestamp': datetime.utcnow().isoformat(),
                'event_id': event_id
            }

            # PHASE 3.2: Emit both 'score_updated' (legacy) and 'live_score_update' (new)
            await self.sio.emit('score_updated', score_data, room=f'event_{event_id}')
            await self.sio.emit('live_score_update', score_data, room=f'event_{event_id}')
            logger.info(f"Score update broadcasted: {score_data}")

            # PERFORMANCE OPTIMIZATION: Schedule debounced leaderboard update
            # This eliminates ~1000ms blocking operation
            self._schedule_leaderboard_update(event_id)

        except Exception as e:
            logger.error(f"Error broadcasting score update: {e}")

    async def broadcast_leaderboard_update(self, event_id: int):
        """Broadcast leaderboard update to all connected clients"""
        await self._broadcast_leaderboard_update(event_id)

    def get_app(self):
        """Get the SocketIO app for integration with FastAPI"""
        return self.sio

    async def get_connected_clients_count(self, event_id: int) -> int:
        """Get number of connected clients for an event"""
        try:
            room = f'event_{event_id}'
            clients = await self.sio.get_session(room)
            return len(clients) if clients else 0
        except Exception as e:
            logger.error(f"Error getting connected clients count: {e}")
            return 0

    async def broadcast_event_status_change(self, event_id: int, is_active: bool):
        """Broadcast event status change to all connected clients"""
        try:
            status_data = {
                'event_id': event_id,
                'is_active': is_active,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            await self.sio.emit('event_status_changed', status_data, room=f'event_{event_id}')
            logger.info(f"Event status change broadcasted: {status_data}")
            
        except Exception as e:
            logger.error(f"Error broadcasting event status change: {e}")

    async def broadcast_participant_update(self, event_id: int, participant_id: int, action: str):
        """Broadcast participant update (added, removed, updated)"""
        try:
            participant = self.session.get(Participant, participant_id)
            if not participant:
                return
            
            update_data = {
                'event_id': event_id,
                'participant_id': participant_id,
                'participant_name': participant.name,
                'action': action,  # 'added', 'removed', 'updated'
                'timestamp': datetime.utcnow().isoformat()
            }
            
            await self.sio.emit('participant_updated', update_data, room=f'event_{event_id}')
            logger.info(f"Participant update broadcasted: {update_data}")
            
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
