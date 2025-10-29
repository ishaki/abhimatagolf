import axios from 'axios';
import { handleAuthError } from '@/utils/authErrorHandler';

// Create API instance for winner configuration
const winnerConfigApi = axios.create({
  baseURL: 'http://localhost:8000/api/v1/winners',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth interceptor
winnerConfigApi.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor
winnerConfigApi.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      handleAuthError();
    }
    return Promise.reject(error);
  }
);

// TypeScript interfaces
export enum TieBreakingMethod {
  STANDARD_GOLF = 'standard_golf',
  SCORECARD_PLAYOFF = 'scorecard_playoff',
  SHARE_POSITION = 'share_position',
  LOWEST_HANDICAP = 'lowest_handicap',
  RANDOM = 'random',
}

export enum CalculationTrigger {
  MANUAL_ONLY = 'manual_only',
  ALL_SCORES_COMPLETE = 'all_scores_complete',
  EVENT_END = 'event_end',
  SCORE_SUBMISSION = 'score_submission',
}

export interface AwardCategory {
  rank: number;
  name: string;
  description: string;
}

export interface AwardCategories {
  overall: AwardCategory[];
  division: AwardCategory[];
}

export interface WinnerConfiguration {
  id: number;
  event_id: number;
  tie_breaking_method: TieBreakingMethod;
  award_categories: AwardCategories;
  winners_per_division: number;
  top_overall_count: number;
  calculation_trigger: CalculationTrigger;
  allow_manual_override: boolean;
  include_best_gross: boolean;
  include_best_net: boolean;
  exclude_incomplete_rounds: boolean;
  minimum_holes_for_ranking: number;
  created_at: string;
  updated_at: string;
  created_by: number;
}

export interface WinnerConfigurationCreate {
  event_id: number;
  tie_breaking_method?: TieBreakingMethod;
  award_categories?: AwardCategories;
  winners_per_division?: number;
  top_overall_count?: number;
  calculation_trigger?: CalculationTrigger;
  allow_manual_override?: boolean;
  include_best_gross?: boolean;
  include_best_net?: boolean;
  exclude_incomplete_rounds?: boolean;
  minimum_holes_for_ranking?: number;
}

export interface WinnerConfigurationUpdate {
  tie_breaking_method?: TieBreakingMethod;
  award_categories?: AwardCategories;
  winners_per_division?: number;
  top_overall_count?: number;
  calculation_trigger?: CalculationTrigger;
  allow_manual_override?: boolean;
  include_best_gross?: boolean;
  include_best_net?: boolean;
  exclude_incomplete_rounds?: boolean;
  minimum_holes_for_ranking?: number;
}

export interface WinnerManualOverride {
  overall_rank?: number;
  division_rank?: number;
  award_category?: string;
  prize_details?: string;
  is_tied?: boolean;
}

// API functions
export const winnerConfigurationService = {
  // Get configuration for an event (creates default if not exists)
  getConfig: async (eventId: number): Promise<WinnerConfiguration> => {
    const response = await winnerConfigApi.get(`/config/${eventId}`);
    return response.data;
  },

  // Create new configuration
  createConfig: async (data: WinnerConfigurationCreate): Promise<WinnerConfiguration> => {
    const response = await winnerConfigApi.post('/config', data);
    return response.data;
  },

  // Update configuration
  updateConfig: async (
    eventId: number,
    data: WinnerConfigurationUpdate
  ): Promise<WinnerConfiguration> => {
    const response = await winnerConfigApi.put(`/config/${eventId}`, data);
    return response.data;
  },

  // Delete configuration
  deleteConfig: async (eventId: number): Promise<void> => {
    await winnerConfigApi.delete(`/config/${eventId}`);
  },

  // Override winner result
  overrideWinner: async (winnerId: number, data: WinnerManualOverride): Promise<any> => {
    const response = await winnerConfigApi.patch(`/${winnerId}/override`, data);
    return response.data;
  },

  // Delete winner result
  deleteWinner: async (winnerId: number): Promise<void> => {
    await winnerConfigApi.delete(`/${winnerId}`);
  },
};

// Helper functions for UI display
export const getTieBreakingMethodLabel = (method: TieBreakingMethod): string => {
  const labels: Record<TieBreakingMethod, string> = {
    [TieBreakingMethod.STANDARD_GOLF]: 'Standard Golf (Back 9, Last 6, Last 3, Last Hole)',
    [TieBreakingMethod.SCORECARD_PLAYOFF]: 'Scorecard Playoff',
    [TieBreakingMethod.SHARE_POSITION]: 'Share Position',
    [TieBreakingMethod.LOWEST_HANDICAP]: 'Lowest Handicap',
    [TieBreakingMethod.RANDOM]: 'Random',
  };
  return labels[method];
};

export const getCalculationTriggerLabel = (trigger: CalculationTrigger): string => {
  const labels: Record<CalculationTrigger, string> = {
    [CalculationTrigger.MANUAL_ONLY]: 'Manual Only',
    [CalculationTrigger.ALL_SCORES_COMPLETE]: 'All Scores Complete',
    [CalculationTrigger.EVENT_END]: 'Event End',
    [CalculationTrigger.SCORE_SUBMISSION]: 'After Score Submission',
  };
  return labels[trigger];
};

