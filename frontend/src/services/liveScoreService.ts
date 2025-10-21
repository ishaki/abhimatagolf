/**
 * Live Score Service - Phase 3.2
 *
 * Public API service for real-time tournament score display.
 * No authentication required.
 */

import api from './api';
import { ScorecardResponse } from './scorecardService';

export type SortBy = 'gross' | 'net';

export interface LiveScoreParams {
  eventId: number;
  sortBy?: SortBy;
}

/**
 * Get live score data for an event (PUBLIC - No auth required)
 *
 * Returns all participants with raw scorecard data sorted by:
 * 1. Holes completed (descending)
 * 2. Gross/Net score (ascending)
 * 3. Participants with zero scores at bottom
 */
export const getLiveScore = async (
  eventId: number,
  sortBy: SortBy = 'gross'
): Promise<ScorecardResponse[]> => {
  const response = await api.get(`/live-score/${eventId}`, {
    params: { sort_by: sortBy },
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
