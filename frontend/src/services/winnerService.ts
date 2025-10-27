import api from './api';

// Types
export interface WinnerResult {
  id: number;
  event_id: number;
  participant_id: number;
  participant_name: string;
  division?: string;
  division_id?: number;
  overall_rank?: number;  // Optional - division winners may not have overall rank
  division_rank?: number;
  gross_score: number;
  net_score?: number;
  declared_handicap: number;
  course_handicap: number;
  system36_handicap?: number;  // System 36 calculated handicap (36 - total points)
  teebox_name?: string;
  teebox_course_rating?: number;
  teebox_slope_rating?: number;
  is_tied: boolean;
  tied_with?: {
    participant_ids: string[];
    score: number;
  };
  tie_break_criteria?: {
    method: string;
    note: string;
  };
  award_category?: string;
  prize_details?: string;
  calculated_at: string;
}

export interface WinnersListResponse {
  event_id: number;
  event_name: string;
  scoring_type: string;  // Event scoring type (stroke, net_stroke, system_36, stableford)
  total_winners: number;
  winners: WinnerResult[];
}

export interface CalculateWinnersRequest {
  event_id: number;
}

// API Functions
export const calculateEventWinners = async (
  eventId: number
): Promise<WinnerResult[]> => {
  const response = await api.post('/winners/calculate', { event_id: eventId });
  return response.data;
};

export const getEventWinners = async (
  eventId: number,
  divisionId?: number,
  topN?: number
): Promise<WinnersListResponse> => {
  const params = new URLSearchParams();

  if (divisionId) params.append('division_id', divisionId.toString());
  if (topN) params.append('top_n', topN.toString());

  const response = await api.get(`/winners/${eventId}?${params}`);
  return response.data;
};

export const getOverallWinner = async (
  eventId: number
): Promise<WinnerResult> => {
  const response = await api.get(`/winners/${eventId}/overall-winner`);
  return response.data;
};

export const getDivisionWinner = async (
  eventId: number,
  divisionId: number
): Promise<WinnerResult> => {
  const response = await api.get(`/winners/${eventId}/division/${divisionId}/winner`);
  return response.data;
};

// Helper functions
export const getRankDisplay = (rank: number): string => {
  if (rank === 1) return '1st';
  if (rank === 2) return '2nd';
  if (rank === 3) return '3rd';
  return `${rank}th`;
};

export const getRankColor = (rank: number): string => {
  if (rank === 1) return 'text-yellow-600 bg-yellow-50 border-yellow-300'; // Gold
  if (rank === 2) return 'text-gray-600 bg-gray-100 border-gray-300'; // Silver
  if (rank === 3) return 'text-orange-600 bg-orange-50 border-orange-300'; // Bronze
  return 'text-gray-700 bg-white border-gray-300';
};

export const getRankBadgeColor = (rank: number): string => {
  if (rank === 1) return 'bg-yellow-500 text-white'; // Gold
  if (rank === 2) return 'bg-gray-400 text-white'; // Silver
  if (rank === 3) return 'bg-orange-500 text-white'; // Bronze
  return 'bg-blue-500 text-white';
};

export const formatTieInformation = (winner: WinnerResult): string => {
  if (!winner.is_tied) return '';

  if (winner.tied_with && winner.tied_with.participant_ids.length > 1) {
    const count = winner.tied_with.participant_ids.length;
    return `Tied with ${count - 1} other${count > 2 ? 's' : ''}`;
  }

  return 'Tied';
};

export const exportParticipantScores = async (eventId: number): Promise<void> => {
  try {
    const response = await api.get(`/winners/${eventId}/export`, {
      responseType: 'blob',
    });

    // Create blob URL and trigger download
    const blob = new Blob([response.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });
    
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    
    // Extract filename from response headers or use default
    const contentDisposition = response.headers['content-disposition'];
    let filename = `Event_${eventId}_Scores.xlsx`;
    
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="(.+)"/);
      if (filenameMatch) {
        filename = filenameMatch[1];
      }
    }
    
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  } catch (error) {
    console.error('Error exporting participant scores:', error);
    throw new Error('Failed to export participant scores');
  }
};