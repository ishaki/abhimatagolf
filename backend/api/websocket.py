"""
WebSocket API Endpoints

Provides WebSocket endpoints for real-time updates in the golf tournament system.
Replaces Socket.IO with native FastAPI WebSockets.
"""

import json
import uuid
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from sqlmodel import Session
from core.database import get_session
from core.websocket_manager import connection_manager, verify_websocket_token
from core.app_logging import logger
from models.event import Event


router = APIRouter(prefix="/api/v1/ws", tags=["WebSocket"])


@router.websocket("/{event_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    event_id: int,
    token: Optional[str] = Query(None, description="JWT token for authentication (optional)"),
    session: Session = Depends(get_session)
):
    """
    WebSocket endpoint for real-time updates
    
    **Purpose**: Provide real-time score updates for live scoring display
    
    **Parameters**:
    - `event_id`: Event ID to subscribe to updates for
    - `token`: Optional JWT token for authentication
    
    **Events**:
    - `score_updated`: Score change notification
    - `live_score_update`: Live score update (alias)
    - `leaderboard_update`: Leaderboard refresh
    - `event_status_changed`: Event active/inactive status
    - `participant_updated`: Participant added/removed/updated
    - `ping`: Heartbeat ping (responds with pong)
    
    **Connection Flow**:
    1. Client connects to `/api/v1/ws/{event_id}`
    2. Server validates event exists
    3. Optional token validation
    4. Client joins event room
    5. Server sends welcome message
    6. Client receives real-time updates
    """
    
    # Generate unique connection ID
    connection_id = str(uuid.uuid4())
    
    try:
        # Validate event exists
        event = session.get(Event, event_id)
        if not event:
            await websocket.close(code=4004, reason="Event not found")
            return
        
        # Verify token if provided
        user_id = None
        if token:
            user_id = verify_websocket_token(token)
            if user_id is None:
                await websocket.close(code=4001, reason="Invalid or expired token")
                return
        
        # Connect to WebSocket manager
        await connection_manager.connect(websocket, connection_id, event_id, user_id)
        
        logger.info(f"WebSocket connected: {connection_id} for event {event_id} (user: {user_id})")
        
        # Main message handling loop
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                message_type = message.get('type')
                
                if message_type == 'ping':
                    # Handle heartbeat ping
                    await connection_manager.handle_ping(connection_id)
                    
                elif message_type == 'join_event':
                    # Client joining event (already handled in connect)
                    await connection_manager.send_personal_message({
                        'type': 'joined_event',
                        'event_id': event_id,
                        'message': f'Joined event {event_id}',
                        'timestamp': connection_manager.connection_metadata[connection_id]['connected_at'].isoformat()
                    }, connection_id)
                    
                elif message_type == 'leave_event':
                    # Client leaving event
                    await connection_manager.send_personal_message({
                        'type': 'left_event',
                        'event_id': event_id,
                        'message': f'Left event {event_id}',
                        'timestamp': connection_manager.connection_metadata[connection_id]['connected_at'].isoformat()
                    }, connection_id)
                    
                else:
                    # Unknown message type
                    await connection_manager.send_personal_message({
                        'type': 'error',
                        'message': f'Unknown message type: {message_type}',
                        'timestamp': connection_manager.connection_metadata[connection_id]['connected_at'].isoformat()
                    }, connection_id)
                    
            except json.JSONDecodeError:
                await connection_manager.send_personal_message({
                    'type': 'error',
                    'message': 'Invalid JSON message',
                    'timestamp': connection_manager.connection_metadata[connection_id]['connected_at'].isoformat()
                }, connection_id)
                
            except WebSocketDisconnect:
                # Client disconnected normally
                break
                
    except WebSocketDisconnect:
        # Client disconnected
        logger.info(f"WebSocket disconnected normally: {connection_id}")
        
    except Exception as e:
        logger.error(f"WebSocket error for {connection_id}: {e}")
        
    finally:
        # Clean up connection
        connection_manager.disconnect(connection_id)


@router.get("/health")
async def websocket_health():
    """WebSocket service health check"""
    return {
        "status": "healthy",
        "active_connections": connection_manager.get_all_connections_count(),
        "event_rooms": len(connection_manager.event_rooms),
        "timestamp": connection_manager.connection_metadata.get('connected_at', 'unknown')
    }


@router.get("/event/{event_id}/connections")
async def get_event_connections(event_id: int):
    """Get number of connected clients for an event"""
    return {
        "event_id": event_id,
        "connected_clients": connection_manager.get_connected_clients_count(event_id)
    }
