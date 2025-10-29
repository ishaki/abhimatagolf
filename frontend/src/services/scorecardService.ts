import api from './api';

// Types
export interface HoleScore {
  hole_number: number;
  strokes: number;
}

export interface ScorecardSubmit {
  participant_id: number;
  scores: HoleScore[];
}

export interface HoleScoreResponse {
  id: number;
  hole_number: number;
  hole_par: number;
  hole_distance: number;
  handicap_index: number;
  strokes: number;
  score_to_par: number;
  color_code: 'eagle' | 'birdie' | 'par' | 'bogey' | 'double_bogey' | 'none';
  system36_points?: number;  // Add System36 points field
}

export interface ScorecardResponse {
  participant_id: number;
  participant_name: string;
  event_id: number;
  event_name: string;
  handicap: number;
  country?: string | null;
  front_nine: HoleScoreResponse[];
  out_total: number;
  out_to_par: number;
  back_nine: HoleScoreResponse[];
  in_total: number;
  in_to_par: number;
  gross_score: number;
  net_score: number;
  score_to_par: number;
  course_par: number;
  holes_completed: number;
  last_updated: string | null;
  recorded_by: string | null;
  system36_points?: number;  // Add System36 points field
}

export interface ScorecardListResponse {
  scorecards: ScorecardResponse[];
  total: number;
}

export interface ScoreUpdate {
  strokes: number;
  reason?: string;
}

export interface ScoreHistoryResponse {
  id: number;
  scorecard_id: number;
  old_strokes: number;
  new_strokes: number;
  modified_by: string;
  modified_at: string;
  reason: string | null;
}

// API Functions
export const submitHoleScore = async (
  participantId: number,
  holeNumber: number,
  strokes: number
): Promise<HoleScoreResponse> => {
  const response = await api.post('/scorecards/', null, {
    params: {
      participant_id: participantId,
      hole_number: holeNumber,
      strokes: strokes,
    },
  });
  return response.data;
};

export const bulkSubmitScores = async (
  data: ScorecardSubmit
): Promise<ScorecardResponse> => {
  const response = await api.post('/scorecards/bulk', data);
  return response.data;
};

export const getParticipantScorecard = async (
  participantId: number
): Promise<ScorecardResponse> => {
  const response = await api.get(`/scorecards/participant/${participantId}`);
  return response.data;
};

export const getEventScorecards = async (
  eventId: number
): Promise<ScorecardListResponse> => {
  const response = await api.get(`/scorecards/event/${eventId}`);
  return response.data;
};

export const updateHoleScore = async (
  scorecardId: number,
  data: ScoreUpdate
): Promise<HoleScoreResponse> => {
  const response = await api.put(`/scorecards/${scorecardId}`, data);
  return response.data;
};

export const deleteHoleScore = async (scorecardId: number): Promise<void> => {
  await api.delete(`/scorecards/${scorecardId}`);
};

export const getScoreHistory = async (
  scorecardId: number
): Promise<ScoreHistoryResponse[]> => {
  const response = await api.get(`/scorecards/${scorecardId}/history`);
  return response.data;
};

// Helper function to get color for score
export const getScoreColor = (colorCode: string): string => {
  const colors: Record<string, string> = {
    eagle: 'text-blue-600 bg-blue-50 border-blue-200',
    birdie: 'text-green-600 bg-green-50 border-green-200',
    par: 'text-gray-600 bg-white border-gray-300',
    bogey: 'text-yellow-600 bg-yellow-50 border-yellow-200',
    double_bogey: 'text-red-600 bg-red-50 border-red-200',
    none: 'text-gray-400 bg-gray-50 border-gray-200',
  };
  return colors[colorCode] || colors.none;
};

// Helper function to format score to par
export const formatScoreToPar = (scoreToPar: number): string => {
  if (scoreToPar === 0) return 'E';
  if (scoreToPar > 0) return `+${scoreToPar}`;
  return scoreToPar.toString();
};
