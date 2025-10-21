import api from './api';

export interface Participant {
  id: number;
  event_id: number;
  name: string;
  declared_handicap: number;
  division?: string;
  division_id?: number;
  registered_at: string;
  event_name?: string;
  scorecard_count?: number;
  total_gross_score?: number;
  total_net_score?: number;
  total_points?: number;
}

export interface ParticipantCreate {
  event_id: number;
  name: string;
  declared_handicap?: number;
  division?: string;
  division_id?: number;
}

export interface ParticipantUpdate {
  name?: string;
  declared_handicap?: number;
  division?: string;
  division_id?: number;
}

export interface ParticipantListResponse {
  participants: Participant[];
  total: number;
  page: number;
  per_page: number;
}

export interface ParticipantFilters {
  page?: number;
  per_page?: number;
  search?: string;
  event_id?: number;
  division?: string;
  division_id?: number;
}

export interface ParticipantBulkCreate {
  event_id: number;
  participants: Array<{
    name: string;
    declared_handicap?: number;
    division?: string;
    division_id?: number;
  }>;
}

export interface ParticipantImportResult {
  success: boolean;
  total_rows: number;
  successful: number;
  failed: number;
  participants: Participant[];
  errors: Array<{ row: number; name: string; error: string }>;
}

export interface ParticipantStats {
  total_participants: number;
  by_division: Record<string, number>;
  average_handicap: number;
}

// Participant API functions
export const getParticipants = async (filters: ParticipantFilters = {}): Promise<ParticipantListResponse> => {
  const params = new URLSearchParams();

  if (filters.page) params.append('page', filters.page.toString());
  if (filters.per_page) params.append('per_page', filters.per_page.toString());
  if (filters.search) params.append('search', filters.search);
  if (filters.event_id) params.append('event_id', filters.event_id.toString());
  if (filters.division) params.append('division', filters.division);
  if (filters.division_id) params.append('division_id', filters.division_id.toString());

  const response = await api.get(`/participants/?${params.toString()}`);
  return response.data;
};

export const getParticipant = async (participantId: number): Promise<Participant> => {
  const response = await api.get(`/participants/${participantId}`);
  return response.data;
};

export const createParticipant = async (participantData: ParticipantCreate): Promise<Participant> => {
  const response = await api.post('/participants/', participantData);
  return response.data;
};

export const updateParticipant = async (participantId: number, participantData: ParticipantUpdate): Promise<Participant> => {
  const response = await api.put(`/participants/${participantId}`, participantData);
  return response.data;
};

export const deleteParticipant = async (participantId: number): Promise<void> => {
  await api.delete(`/participants/${participantId}`);
};

export const createParticipantsBulk = async (data: ParticipantBulkCreate): Promise<Participant[]> => {
  const response = await api.post('/participants/bulk', data);
  return response.data;
};

export const uploadParticipants = async (eventId: number, file: File): Promise<ParticipantImportResult> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post(`/participants/upload?event_id=${eventId}`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const getEventParticipants = async (eventId: number): Promise<Participant[]> => {
  const response = await api.get(`/participants/event/${eventId}/list`);
  return response.data;
};

export const getParticipantStats = async (eventId: number): Promise<ParticipantStats> => {
  const response = await api.get(`/participants/event/${eventId}/stats`);
  return response.data;
};

export const getEventDivisions = async (eventId: number): Promise<string[]> => {
  const response = await api.get(`/participants/event/${eventId}/divisions`);
  return response.data;
};
