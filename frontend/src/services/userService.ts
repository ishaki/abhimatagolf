import api from './authService';

export interface User {
  id: number;
  full_name: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface UserCreate {
  full_name: string;
  email: string;
  password: string;
  role: string;
  is_active: boolean;
}

export interface UserUpdate {
  full_name?: string;
  email?: string;
  role?: string;
  is_active?: boolean;
}

export interface UserListResponse {
  users: User[];
  total: number;
  page: number;
  per_page: number;
}

export const getUsers = async (page: number = 1, per_page: number = 20, search?: string): Promise<UserListResponse> => {
  const params = new URLSearchParams({
    page: page.toString(),
    per_page: per_page.toString(),
  });

  if (search) {
    params.append('search', search);
  }

  const response = await api.get(`/users?${params.toString()}`);
  return response.data;
};

export const getUser = async (id: number): Promise<User> => {
  const response = await api.get(`/users/${id}`);
  return response.data;
};

export const createUser = async (userData: UserCreate): Promise<User> => {
  const response = await api.post('/users', userData);
  return response.data;
};

export const updateUser = async (id: number, userData: UserUpdate): Promise<User> => {
  const response = await api.put(`/users/${id}`, userData);
  return response.data;
};

export const deleteUser = async (id: number): Promise<void> => {
  await api.delete(`/users/${id}`);
};

// Event User interfaces
export interface EventUser {
  user: User;
  access_level: string;
  assigned_at: string;
}

export interface EventUserCreateData {
  full_name: string;
  email?: string;
  password?: string;
}

export interface EventUserCreateResponse {
  user: User;
  email: string;
  password: string;
  message: string;
}

export interface EventUsersListResponse {
  users: EventUser[];
  total: number;
}

// Event User functions
export const createEventUser = async (eventId: number, userData: EventUserCreateData): Promise<EventUserCreateResponse> => {
  const response = await api.post(`/users/event/${eventId}/create`, userData);
  return response.data;
};

export const getEventUsers = async (eventId: number): Promise<EventUsersListResponse> => {
  const response = await api.get(`/users/event/${eventId}`);
  return response.data;
};

export const removeEventUser = async (eventId: number, userId: number): Promise<void> => {
  await api.delete(`/users/event/${eventId}/user/${userId}`);
};