"""
WebSocket Connection Manager

Manages WebSocket connections for real-time updates in the golf tournament system.
Replaces Socket.IO with native FastAPI WebSockets for better integration.
"""

import json
import asyncio
from typing import Dict, List, Set, Optional, Any
from datetime import datetime
import jwt
from fastapi import WebSocket, WebSocketDisconnect
from sqlmodel import Session
from core.app_logging import logger
from core.config import settings


class ConnectionManager:
    """Manages WebSocket connections and event-based rooms"""
    
    def __init__(self):
        # Active connections: {connection_id: WebSocket}
        self.active_connections: Dict[str, WebSocket] = {}
        
        # Event rooms: {event_id: Set[connection_id]}
        self.event_rooms: Dict[int, Set[str]] = {}
        
        # Connection metadata: {connection_id: {'event_id': int, 'user_id': Optional[int]}}
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Heartbeat tracking for connection health
        self.last_ping: Dict[str, datetime] = {}
        
    async def connect(self, websocket: WebSocket, connection_id: str, event_id: int, user_id: Optional[int] = None):
        """Accept WebSocket connection and join event room"""
        try:
            await websocket.accept()
            self.active_connections[connection_id] = websocket
            
            # Join event room
            if event_id not in self.event_rooms:
                self.event_rooms[event_id] = set()
            self.event_rooms[event_id].add(connection_id)
            
            # Store metadata
            self.connection_metadata[connection_id] = {
                'event_id': event_id,
                'user_id': user_id,
                'connected_at': datetime.utcnow()
            }
            
            # Initialize heartbeat
            self.last_ping[connection_id] = datetime.utcnow()
            
            logger.info(f"WebSocket connected: {connection_id} for event {event_id}")
            
            # Send welcome message
            await self.send_personal_message({
                'type': 'connected',
                'message': 'Connected to live scoring',
                'event_id': event_id,
                'timestamp': datetime.utcnow().isoformat()
            }, connection_id)
            
        except Exception as e:
            logger.error(f"Error accepting WebSocket connection: {e}")
            raise
    
    def disconnect(self, connection_id: str):
        """Remove connection and clean up metadata"""
        try:
            # Remove from event room
            if connection_id in self.connection_metadata:
                event_id = self.connection_metadata[connection_id].get('event_id')
                if event_id and event_id in self.event_rooms:
                    self.event_rooms[event_id].discard(connection_id)
                    
                    # Clean up empty rooms
                    if not self.event_rooms[event_id]:
                        del self.event_rooms[event_id]
            
            # Remove connection and metadata
            self.active_connections.pop(connection_id, None)
            self.connection_metadata.pop(connection_id, None)
            self.last_ping.pop(connection_id, None)
            
            logger.info(f"WebSocket disconnected: {connection_id}")
            
        except Exception as e:
            logger.error(f"Error disconnecting WebSocket: {e}")
    
    async def send_personal_message(self, message: dict, connection_id: str):
        """Send message to specific connection"""
        try:
            if connection_id in self.active_connections:
                websocket = self.active_connections[connection_id]
                await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending personal message to {connection_id}: {e}")
            # Remove failed connection
            self.disconnect(connection_id)
    
    async def broadcast_to_event(self, message: dict, event_id: int):
        """Broadcast message to all connections in an event room"""
        if event_id not in self.event_rooms:
            return
        
        # Get connections to broadcast to (copy to avoid modification during iteration)
        connections_to_broadcast = list(self.event_rooms[event_id])
        
        for connection_id in connections_to_broadcast:
            try:
                await self.send_personal_message(message, connection_id)
            except Exception as e:
                logger.error(f"Error broadcasting to {connection_id}: {e}")
                # Connection will be cleaned up in send_personal_message
    
    async def broadcast_score_update(self, event_id: int, participant_id: int, participant_name: str, 
                                   hole_number: int, strokes: int):
        """Broadcast score update to event room"""
        message = {
            'type': 'score_updated',
            'data': {
                'participant_id': participant_id,
                'participant_name': participant_name,
                'hole_number': hole_number,
                'strokes': strokes,
                'timestamp': datetime.utcnow().isoformat(),
                'event_id': event_id
            }
        }
        
        await self.broadcast_to_event(message, event_id)
        logger.info(f"Score update broadcasted to event {event_id}: {message}")
    
    async def broadcast_live_score_update(self, event_id: int, participant_id: int, participant_name: str,
                                         hole_number: int, strokes: int):
        """Broadcast live score update (alias for score_updated)"""
        message = {
            'type': 'live_score_update',
            'data': {
                'participant_id': participant_id,
                'participant_name': participant_name,
                'hole_number': hole_number,
                'strokes': strokes,
                'timestamp': datetime.utcnow().isoformat(),
                'event_id': event_id
            }
        }
        
        await self.broadcast_to_event(message, event_id)
        logger.info(f"Live score update broadcasted to event {event_id}: {message}")
    
    async def broadcast_leaderboard_update(self, event_id: int, leaderboard_data: dict):
        """Broadcast leaderboard update to event room"""
        message = {
            'type': 'leaderboard_update',
            'data': {
                'event_id': event_id,
                'leaderboard': leaderboard_data,
                'timestamp': datetime.utcnow().isoformat()
            }
        }
        
        await self.broadcast_to_event(message, event_id)
        logger.info(f"Leaderboard update broadcasted to event {event_id}")
    
    async def broadcast_event_status_change(self, event_id: int, is_active: bool):
        """Broadcast event status change"""
        message = {
            'type': 'event_status_changed',
            'data': {
                'event_id': event_id,
                'is_active': is_active,
                'timestamp': datetime.utcnow().isoformat()
            }
        }
        
        await self.broadcast_to_event(message, event_id)
        logger.info(f"Event status change broadcasted to event {event_id}")
    
    async def broadcast_participant_update(self, event_id: int, participant_id: int, 
                                         participant_name: str, action: str):
        """Broadcast participant update (added, removed, updated)"""
        message = {
            'type': 'participant_updated',
            'data': {
                'event_id': event_id,
                'participant_id': participant_id,
                'participant_name': participant_name,
                'action': action,
                'timestamp': datetime.utcnow().isoformat()
            }
        }
        
        await self.broadcast_to_event(message, event_id)
        logger.info(f"Participant update broadcasted to event {event_id}")
    
    async def handle_ping(self, connection_id: str):
        """Handle ping message for connection health"""
        try:
            self.last_ping[connection_id] = datetime.utcnow()
            await self.send_personal_message({
                'type': 'pong',
                'timestamp': datetime.utcnow().isoformat()
            }, connection_id)
        except Exception as e:
            logger.error(f"Error handling ping for {connection_id}: {e}")
    
    def get_connected_clients_count(self, event_id: int) -> int:
        """Get number of connected clients for an event"""
        if event_id not in self.event_rooms:
            return 0
        return len(self.event_rooms[event_id])
    
    def get_all_connections_count(self) -> int:
        """Get total number of active connections"""
        return len(self.active_connections)
    
    async def cleanup_stale_connections(self):
        """Remove connections that haven't pinged recently"""
        current_time = datetime.utcnow()
        stale_connections = []
        
        for connection_id, last_ping_time in self.last_ping.items():
            # Consider connection stale if no ping in last 60 seconds
            if (current_time - last_ping_time).total_seconds() > 60:
                stale_connections.append(connection_id)
        
        for connection_id in stale_connections:
            logger.warning(f"Removing stale connection: {connection_id}")
            self.disconnect(connection_id)


# Global connection manager instance
connection_manager = ConnectionManager()


def verify_websocket_token(token: str) -> Optional[int]:
    """Verify JWT token and return user ID if valid"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        return payload.get('sub')
    except jwt.ExpiredSignatureError:
        logger.warning("WebSocket connection with expired token")
        return None
    except jwt.InvalidTokenError:
        logger.warning("WebSocket connection with invalid token")
        return None
