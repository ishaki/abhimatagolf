import api from './api';

// Types
export interface LeaderboardEntry {
  rank: number;
  participant_id: number;
  participant_name: string;
  handicap: number;
  division?: string;
  division_id?: number;
  gross_score: number;
  net_score: number;
  score_to_par: number;
  holes_completed: number;
  thru: string;
  last_updated?: string;
  system36_points?: number;      // Add for System36
  system36_handicap?: number;    // Add for System36
}

export interface LeaderboardResponse {
  event_id: number;
  event_name: string;
  course_name: string;
  scoring_type: 'stroke' | 'net_stroke' | 'system_36' | 'stableford';
  course_par: number;
  entries: LeaderboardEntry[];
  total_participants: number;
  participants_with_scores: number;
  last_updated: string;
  cache_timestamp?: string;
}

export interface PublicLeaderboardResponse {
  event_id: number;
  event_name: string;
  course_name: string;
  scoring_type: 'stroke' | 'net_stroke' | 'system_36' | 'stableford';
  entries: LeaderboardEntry[];
  total_participants: number;
  last_updated: string;
}

export interface LeaderboardStats {
  total_participants: number;
  participants_with_scores: number;
  average_score: number;
  low_score: number;
  high_score: number;
  cut_line?: number;
  leader_margin?: number;
}

export interface LeaderboardFilters {
  division_id?: number;
  division_name?: string;
  min_holes?: number;
  max_rank?: number;
}

// API Functions
export const getEventLeaderboard = async (
  eventId: number,
  filters?: LeaderboardFilters,
  useCache: boolean = true
): Promise<LeaderboardResponse> => {
  const params = new URLSearchParams();
  
  if (filters?.division_id) params.append('division_id', filters.division_id.toString());
  if (filters?.division_name) params.append('division_name', filters.division_name);
  if (filters?.min_holes) params.append('min_holes', filters.min_holes.toString());
  if (filters?.max_rank) params.append('max_rank', filters.max_rank.toString());
  params.append('use_cache', useCache.toString());

  const response = await api.get(`/leaderboards/event/${eventId}?${params}`);
  return response.data;
};

export const getPublicLeaderboard = async (
  eventId: number,
  filters?: LeaderboardFilters
): Promise<PublicLeaderboardResponse> => {
  const params = new URLSearchParams();
  
  if (filters?.division_id) params.append('division_id', filters.division_id.toString());
  if (filters?.division_name) params.append('division_name', filters.division_name);
  if (filters?.min_holes) params.append('min_holes', filters.min_holes.toString());
  if (filters?.max_rank) params.append('max_rank', filters.max_rank.toString());

  const response = await api.get(`/leaderboards/public/event/${eventId}?${params}`);
  return response.data;
};

export const getLeaderboardStats = async (eventId: number): Promise<LeaderboardStats> => {
  const response = await api.get(`/leaderboards/event/${eventId}/stats`);
  return response.data;
};

export const invalidateLeaderboardCache = async (eventId: number): Promise<void> => {
  await api.post(`/leaderboards/event/${eventId}/invalidate-cache`);
};

// Helper functions
export const formatScoreToPar = (scoreToPar: number): string => {
  if (scoreToPar === 0) return 'E';
  if (scoreToPar > 0) return `+${scoreToPar}`;
  return scoreToPar.toString();
};

export const getRankColor = (rank: number): string => {
  if (rank === 1) return 'text-yellow-600 bg-yellow-50 border-yellow-200'; // Gold
  if (rank === 2) return 'text-gray-600 bg-gray-50 border-gray-200'; // Silver
  if (rank === 3) return 'text-orange-600 bg-orange-50 border-orange-200'; // Bronze
  return 'text-gray-600 bg-white border-gray-300';
};

export const getScoreColor = (scoreToPar: number): string => {
  if (scoreToPar <= -2) return 'text-blue-600 bg-blue-50 border-blue-200'; // Eagle or better
  if (scoreToPar === -1) return 'text-green-600 bg-green-50 border-green-200'; // Birdie
  if (scoreToPar === 0) return 'text-gray-600 bg-white border-gray-300'; // Par
  if (scoreToPar === 1) return 'text-yellow-600 bg-yellow-50 border-yellow-200'; // Bogey
  if (scoreToPar >= 2) return 'text-red-600 bg-red-50 border-red-200'; // Double bogey or worse
  return 'text-gray-400 bg-gray-50 border-gray-200';
};

export const formatLastUpdated = (lastUpdated: string): string => {
  const date = new Date(lastUpdated);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / (1000 * 60));
  
  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  
  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays}d ago`;
};
