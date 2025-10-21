import { create } from 'zustand'
import { loginUser } from '@/services/authService'

interface User {
  id: number
  full_name: string
  email: string
  role: 'super_admin' | 'event_admin' | 'event_user'
  is_active: boolean
  created_at: string
  updated_at: string
}

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
}

interface AuthActions {
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  setUser: (user: User) => void
  setToken: (token: string) => void
  setLoading: (loading: boolean) => void
}

export const useAuthStore = create<AuthState & AuthActions>((set) => ({
  user: JSON.parse(localStorage.getItem('user') || 'null'),
  token: localStorage.getItem('access_token'),
  isAuthenticated: !!localStorage.getItem('access_token'),
  isLoading: false,

  login: async (email: string, password: string) => {
    set({ isLoading: true })
    try {
      const data = await loginUser(email, password)
      const token = data.access_token

      // Store token and user info
      localStorage.setItem('access_token', token)
      localStorage.setItem('user', JSON.stringify(data.user))
      
      set({
        user: data.user,
        token,
        isAuthenticated: true,
        isLoading: false,
      })
    } catch (error) {
      set({ isLoading: false })
      throw error
    }
  },

  logout: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
    set({
      user: null,
      token: null,
      isAuthenticated: false,
    })
  },

  setUser: (user: User) => {
    set({ user })
  },

  setToken: (token: string) => {
    localStorage.setItem('access_token', token)
    set({ token, isAuthenticated: true })
  },

  setLoading: (loading: boolean) => {
    set({ isLoading: loading })
  },
}))
