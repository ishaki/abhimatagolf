import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface EventDivision {
  id: number;
  event_id: number;
  name: string;
  description?: string;
  handicap_min?: number;
  handicap_max?: number;
  max_participants?: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  participant_count?: number;
}

export interface EventDivisionCreate {
  event_id: number;
  name: string;
  description?: string;
  handicap_min?: number;
  handicap_max?: number;
  max_participants?: number;
  is_active?: boolean;
}

export interface EventDivisionUpdate {
  name?: string;
  description?: string;
  handicap_min?: number;
  handicap_max?: number;
  max_participants?: number;
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
  private baseUrl = `${API_BASE_URL}/api/event-divisions`;

  async getDivisionsForEvent(eventId: number): Promise<EventDivision[]> {
    const response = await axios.get(`${this.baseUrl}/event/${eventId}`);
    return response.data;
  }

  async getDivision(divisionId: number): Promise<EventDivision> {
    const response = await axios.get(`${this.baseUrl}/${divisionId}`);
    return response.data;
  }

  async createDivision(divisionData: EventDivisionCreate): Promise<EventDivision> {
    const response = await axios.post(this.baseUrl, divisionData);
    return response.data;
  }

  async createDivisionsBulk(bulkData: EventDivisionBulkCreate): Promise<EventDivision[]> {
    const response = await axios.post(`${this.baseUrl}/bulk`, bulkData);
    return response.data;
  }

  async updateDivision(divisionId: number, divisionData: EventDivisionUpdate): Promise<EventDivision> {
    const response = await axios.put(`${this.baseUrl}/${divisionId}`, divisionData);
    return response.data;
  }

  async deleteDivision(divisionId: number): Promise<void> {
    await axios.delete(`${this.baseUrl}/${divisionId}`);
  }

  async getDivisionStats(eventId: number): Promise<DivisionStats> {
    const response = await axios.get(`${this.baseUrl}/event/${eventId}/stats`);
    return response.data;
  }
}

export const eventDivisionService = new EventDivisionService();
