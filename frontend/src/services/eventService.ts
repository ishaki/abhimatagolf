import axios from 'axios';
import { handleAuthError } from '@/utils/authErrorHandler';

// Create a separate API instance for events since they use different base URL
const eventsApi = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth interceptor for events API
eventsApi.interceptors.request.use(
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

// Add response interceptor for events API
eventsApi.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      handleAuthError();
    }
    return Promise.reject(error);
  }
);

export interface Event {
  id: number;
  name: string;
  description?: string;
  event_date: string;
  course_id: number;
  created_by: number;
  scoring_type: 'stroke' | 'net_stroke' | 'system_36' | 'stableford';
  divisions_config?: Record<string, any>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  course_name?: string;
  creator_name?: string;
  participant_count?: number;
}

export interface EventCreate {
  name: string;
  description?: string;
  event_date: string;
  course_id: number;
  scoring_type: 'stroke' | 'net_stroke' | 'system_36' | 'stableford';
  is_active?: boolean;
}

export interface EventUpdate {
  name?: string;
  description?: string;
  event_date?: string;
  course_id?: number;
  scoring_type?: 'stroke' | 'net_stroke' | 'system_36' | 'stableford';
  divisions_config?: Record<string, any>;
  is_active?: boolean;
}

export interface EventListResponse {
  events: Event[];
  total: number;
  page: number;
  per_page: number;
}

export interface EventStats {
  total_events: number;
  active_events: number;
  upcoming_events: number;
  completed_events: number;
}

export interface EventFilters {
  page?: number;
  per_page?: number;
  search?: string;
  course_id?: number;
  scoring_type?: string;
  is_active?: boolean;
}

// Event API functions
export const getEvents = async (filters: EventFilters = {}): Promise<EventListResponse> => {
  const params = new URLSearchParams();
  
  if (filters.page) params.append('page', filters.page.toString());
  if (filters.per_page) params.append('per_page', filters.per_page.toString());
  if (filters.search) params.append('search', filters.search);
  if (filters.course_id) params.append('course_id', filters.course_id.toString());
  if (filters.scoring_type) params.append('scoring_type', filters.scoring_type);
  if (filters.is_active !== undefined) params.append('is_active', filters.is_active.toString());

  const response = await eventsApi.get(`/api/v1/events/?${params.toString()}`);
  return response.data;
};

export const getEvent = async (eventId: number): Promise<Event> => {
  const response = await eventsApi.get(`/api/v1/events/${eventId}`);
  return response.data;
};

export const createEvent = async (eventData: EventCreate): Promise<Event> => {
  const response = await eventsApi.post('/api/v1/events/', eventData);
  return response.data;
};

export const updateEvent = async (eventId: number, eventData: EventUpdate): Promise<Event> => {
  const response = await eventsApi.put(`/api/v1/events/${eventId}`, eventData);
  return response.data;
};

export const deleteEvent = async (eventId: number): Promise<void> => {
  await eventsApi.delete(`/api/v1/events/${eventId}`);
};

export const getEventStats = async (): Promise<EventStats> => {
  const response = await eventsApi.get('/api/v1/events/stats/overview');
  return response.data;
};

export const duplicateEvent = async (eventId: number, newName: string, newDate: string): Promise<Event> => {
  const response = await eventsApi.post(`/api/v1/events/${eventId}/duplicate`, {
    new_name: newName,
    new_date: newDate
  });
  return response.data;
};

// Re-export getParticipantStats from participantService for convenience
export { getParticipantStats } from './participantService';

