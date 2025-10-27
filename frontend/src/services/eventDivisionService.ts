import axios from 'axios';
import { handleAuthError } from '@/utils/authErrorHandler';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create authenticated axios instance for event divisions
const eventDivisionsApi = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth interceptor
eventDivisionsApi.interceptors.request.use(
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

// Add response interceptor to handle authentication errors
eventDivisionsApi.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      handleAuthError();
    }
    return Promise.reject(error);
  }
);

export interface Teebox {
  id: number;
  course_id: number;
  name: string;
  course_rating: number;
  slope_rating: number;
  created_at: string;
  updated_at: string;
}

export interface EventDivision {
  id: number;
  event_id: number;
  name: string;
  description?: string;
  division_type?: 'men' | 'women' | 'senior' | 'vip' | 'mixed';
  parent_division_id?: number | null;  // NEW: For sub-divisions
  is_auto_assigned?: boolean;          // NEW: True for auto-assigned sub-divisions
  handicap_min?: number;
  handicap_max?: number;
  use_course_handicap_for_assignment?: boolean;
  max_participants?: number;
  teebox_id?: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  participant_count?: number;
  teebox?: Teebox;
  sub_divisions?: EventDivisionTree[];  // NEW: Nested sub-divisions for tree view
}

// NEW: Hierarchical division structure
export interface EventDivisionTree {
  id: number;
  event_id: number;
  name: string;
  description?: string;
  division_type?: 'men' | 'women' | 'senior' | 'vip' | 'mixed';
  parent_division_id?: number | null;
  is_auto_assigned: boolean;
  handicap_min?: number;
  handicap_max?: number;
  max_participants?: number;
  teebox_id?: number;
  sub_divisions: EventDivisionTree[];  // Recursive structure
}

export interface EventDivisionCreate {
  event_id: number;
  name: string;
  description?: string;
  division_type?: 'men' | 'women' | 'senior' | 'vip' | 'mixed';
  handicap_min?: number;
  handicap_max?: number;
  use_course_handicap_for_assignment?: boolean;
  max_participants?: number;
  teebox_id?: number;
  is_active?: boolean;
}

export interface EventDivisionUpdate {
  name?: string;
  description?: string;
  division_type?: 'men' | 'women' | 'senior' | 'vip' | 'mixed';
  handicap_min?: number;
  handicap_max?: number;
  use_course_handicap_for_assignment?: boolean;
  max_participants?: number;
  teebox_id?: number;
  is_active?: boolean;
}

export interface EventDivisionBulkCreate {
  event_id: number;
  divisions: Omit<EventDivisionCreate, 'event_id'>[];
}

export interface DivisionStats {
  total_divisions: number;
  active_divisions: number;
  total_participants: number;
  divisions: Array<{
    id: number;
    name: string;
    participant_count: number;
    max_participants?: number;
    is_full: boolean;
  }>;
}

class EventDivisionService {
  async getDivisionsForEvent(eventId: number): Promise<EventDivision[]> {
    const response = await eventDivisionsApi.get(`/event-divisions/event/${eventId}`);
    return response.data;
  }

  async getDivision(divisionId: number): Promise<EventDivision> {
    const response = await eventDivisionsApi.get(`/event-divisions/${divisionId}`);
    return response.data;
  }

  async createDivision(divisionData: EventDivisionCreate): Promise<EventDivision> {
    const response = await eventDivisionsApi.post('/event-divisions', divisionData);
    return response.data;
  }

  async createDivisionsBulk(bulkData: EventDivisionBulkCreate): Promise<EventDivision[]> {
    const response = await eventDivisionsApi.post('/event-divisions/bulk', bulkData);
    return response.data;
  }

  async updateDivision(divisionId: number, divisionData: EventDivisionUpdate): Promise<EventDivision> {
    const response = await eventDivisionsApi.put(`/event-divisions/${divisionId}`, divisionData);
    return response.data;
  }

  async deleteDivision(divisionId: number): Promise<void> {
    await eventDivisionsApi.delete(`/event-divisions/${divisionId}`);
  }

  async getDivisionStats(eventId: number): Promise<DivisionStats> {
    const response = await eventDivisionsApi.get(`/event-divisions/event/${eventId}/stats`);
    return response.data;
  }

  async assignMenDivisionsByCourseHandicap(eventId: number): Promise<{
    total: number;
    assigned: number;
    skipped: number;
    errors: Array<{participant_name: string; reason: string}>;
  }> {
    const response = await eventDivisionsApi.post('/assign-men-divisions-by-course-handicap', {
      event_id: eventId
    });
    return response.data;
  }

  // ==================== SUB-DIVISION METHODS ====================

  /**
   * Get hierarchical division structure for an event.
   * Returns divisions with nested sub-divisions.
   */
  async getDivisionsTree(eventId: number): Promise<EventDivisionTree[]> {
    const response = await eventDivisionsApi.get(`/event-divisions/event/${eventId}/tree`);
    return response.data;
  }

  /**
   * Create a sub-division under a parent division.
   * For Net Stroke and System 36 Modified events.
   */
  async createSubdivision(data: {
    parent_division_id: number;
    name: string;
    handicap_min?: number;
    handicap_max?: number;
    description?: string;
  }): Promise<EventDivision> {
    const response = await eventDivisionsApi.post('/event-divisions/subdivisions', null, {
      params: data
    });
    return response.data;
  }

  /**
   * Delete a sub-division (only if no participants assigned).
   */
  async deleteSubdivision(subdivisionId: number): Promise<void> {
    await eventDivisionsApi.delete(`/event-divisions/subdivisions/${subdivisionId}`);
  }

  /**
   * Auto-assign participants to pre-defined sub-divisions based on declared handicap.
   * For Net Stroke and System 36 Modified events.
   */
  async autoAssignSubdivisions(eventId: number): Promise<{
    total: number;
    assigned: number;
    skipped: number;
    errors: Array<{participant_name: string; reason: string}>;
  }> {
    const response = await eventDivisionsApi.post(`/event-divisions/event/${eventId}/auto-assign-subdivisions`);
    return response.data;
  }
}

export const eventDivisionService = new EventDivisionService();
