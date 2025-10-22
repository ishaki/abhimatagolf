/**
 * Live Score Service - Phase 3.2
 *
 * Public API service for real-time tournament score display.
 * No authentication required.
 * 
 * Updated to use native WebSocket instead of Socket.IO for better FastAPI integration.
 */

import api from './api';
import { ScorecardResponse } from './scorecardService';

export type SortBy = 'gross' | 'net';

export interface LiveScoreParams {
  eventId: number;
  sortBy?: SortBy;
  filterEmpty?: boolean;
}

/**
 * WebSocket connection helper for live score updates
 */
export class LiveScoreWebSocket {
  private ws: WebSocket | null = null;
  private eventId: number;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // Start with 1 second
  private pingInterval: NodeJS.Timeout | null = null;
  private isConnected = false;
  
  // Event handlers
  private onConnect?: () => void;
  private onDisconnect?: () => void;
  private onError?: (error: Event) => void;
  private onScoreUpdate?: (data: any) => void;
  private onLiveScoreUpdate?: (data: any) => void;
  private onLeaderboardUpdate?: (data: any) => void;

  constructor(eventId: number) {
    this.eventId = eventId;
  }

  connect(token?: string): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        const wsUrl = baseUrl.replace('http://', 'ws://').replace('https://', 'wss://');
        const url = token 
          ? `${wsUrl}/api/v1/ws/${this.eventId}?token=${encodeURIComponent(token)}`
          : `${wsUrl}/api/v1/ws/${this.eventId}`;

        this.ws = new WebSocket(url);
        
        this.ws.onopen = () => {
          console.log('WebSocket connected for live score');
          this.isConnected = true;
          this.reconnectAttempts = 0;
          this.startPingInterval();
          this.onConnect?.();
          resolve();
        };

        this.ws.onclose = (event) => {
          console.log('WebSocket disconnected:', event.code, event.reason);
          this.isConnected = false;
          this.stopPingInterval();
          this.onDisconnect?.();
          
          // Attempt reconnection if not a normal closure
          if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.scheduleReconnect(token);
          }
        };

        this.ws.onerror = (error) => {
          console.warn('WebSocket connection failed, live score will work without real-time updates:', error);
          this.onError?.(error);
          reject(error);
        };

        this.ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

      } catch (error) {
        reject(error);
      }
    });
  }

  private handleMessage(message: any) {
    switch (message.type) {
      case 'connected':
        console.log('WebSocket connected:', message.message);
        break;
      case 'score_updated':
        console.log('Score updated:', message.data);
        this.onScoreUpdate?.(message.data);
        break;
      case 'live_score_update':
        console.log('Live score update:', message.data);
        this.onLiveScoreUpdate?.(message.data);
        break;
      case 'leaderboard_update':
        console.log('Leaderboard update:', message.data);
        this.onLeaderboardUpdate?.(message.data);
        break;
      case 'pong':
        // Heartbeat response
        break;
      case 'error':
        console.error('WebSocket error:', message.message);
        break;
      default:
        console.log('Unknown WebSocket message:', message);
    }
  }

  private startPingInterval() {
    this.pingInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000); // Ping every 30 seconds
  }

  private stopPingInterval() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  private scheduleReconnect(token?: string) {
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1); // Exponential backoff
    
    console.log(`Scheduling WebSocket reconnection attempt ${this.reconnectAttempts} in ${delay}ms`);
    
    setTimeout(() => {
      this.connect(token).catch(error => {
        console.error('Reconnection failed:', error);
      });
    }, delay);
  }

  disconnect() {
    this.stopPingInterval();
    if (this.ws) {
      this.ws.close(1000, 'Client disconnecting');
      this.ws = null;
    }
    this.isConnected = false;
  }

  // Event handler setters
  setOnConnect(handler: () => void) {
    this.onConnect = handler;
  }

  setOnDisconnect(handler: () => void) {
    this.onDisconnect = handler;
  }

  setOnError(handler: (error: Event) => void) {
    this.onError = handler;
  }

  setOnScoreUpdate(handler: (data: any) => void) {
    this.onScoreUpdate = handler;
  }

  setOnLiveScoreUpdate(handler: (data: any) => void) {
    this.onLiveScoreUpdate = handler;
  }

  setOnLeaderboardUpdate(handler: (data: any) => void) {
    this.onLeaderboardUpdate = handler;
  }

  getConnectionState(): number {
    return this.ws?.readyState ?? WebSocket.CLOSED;
  }

  isWebSocketConnected(): boolean {
    return this.isConnected && this.ws?.readyState === WebSocket.OPEN;
  }
}

/**
 * Get live score data for an event (PUBLIC - No auth required)
 *
 * Returns all participants with raw scorecard data sorted by:
 * 1. Holes completed (descending)
 * 2. Gross/Net score (ascending)
 * 3. Participants with zero scores at bottom (unless filtered out)
 */
export const getLiveScore = async (
  eventId: number,
  sortBy: SortBy = 'gross',
  filterEmpty: boolean = false
): Promise<ScorecardResponse[]> => {
  const response = await api.get(`/live-score/${eventId}`, {
    params: { 
      sort_by: sortBy,
      filter_empty: filterEmpty
    },
  });
  return response.data;
};

/**
 * WebSocket event types for live score updates
 */
export interface LiveScoreUpdateEvent {
  participant_id: number;
  participant_name: string;
  hole_number: number;
  strokes: number;
  timestamp: string;
  event_id: number;
}

export interface LeaderboardUpdateEvent {
  // Leaderboard data structure
  event_id: number;
  divisions: any[];
  timestamp: string;
}
