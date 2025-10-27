import axios from 'axios'
import { handleAuthError } from '@/utils/authErrorHandler'
import { willTokenExpireSoon, isTokenExpired } from '@/utils/jwtUtils'
import { toast } from 'sonner'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// Create axios instance
const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Flag to prevent multiple refresh attempts
let isRefreshing = false
let refreshPromise: Promise<string> | null = null

/**
 * Refresh the access token
 * Returns the new token or throws an error
 */
const refreshAccessToken = async (): Promise<string> => {
  const token = localStorage.getItem('access_token')

  if (!token) {
    throw new Error('No token to refresh')
  }

  try {
    const response = await axios.post(
      `${API_BASE_URL}/api/v1/auth/refresh`,
      {},
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    )

    const { access_token } = response.data
    localStorage.setItem('access_token', access_token)

    return access_token
  } catch (error) {
    // Refresh failed - clear tokens and logout
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    throw error
  }
}

// Request interceptor to add auth token and handle proactive refresh
api.interceptors.request.use(
  async (config) => {
    const token = localStorage.getItem('access_token')

    if (token) {
      // Check if token is already expired
      if (isTokenExpired(token)) {
        console.warn('Token already expired, logging out...')
        handleAuthError()
        return Promise.reject(new Error('Token expired'))
      }

      // Check if token will expire soon (within 5 minutes)
      if (willTokenExpireSoon(token, 300)) {
        console.log('Token expiring soon, refreshing...')

        // Prevent multiple concurrent refresh requests
        if (!isRefreshing) {
          isRefreshing = true
          refreshPromise = refreshAccessToken()
            .then((newToken) => {
              isRefreshing = false
              refreshPromise = null
              return newToken
            })
            .catch((error) => {
              isRefreshing = false
              refreshPromise = null
              handleAuthError()
              throw error
            })
        }

        try {
          const newToken = await refreshPromise
          config.headers.Authorization = `Bearer ${newToken}`
        } catch (error) {
          return Promise.reject(error)
        }
      } else {
        config.headers.Authorization = `Bearer ${token}`
      }
    }

    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle 401 errors
api.interceptors.response.use(
  (response) => {
    return response
  },
  async (error) => {
    // Handle 401 Unauthorized errors
    if (error.response?.status === 401) {
      const errorMessage = error.response?.data?.detail || 'Session expired'

      // Show user-friendly message
      toast.error('Session Expired', {
        description: 'Please log in again to continue.',
        duration: 5000,
      })

      // Use centralized error handler to logout
      handleAuthError()

      // Don't retry - just reject
      return Promise.reject(error)
    }

    // Handle other errors normally
    return Promise.reject(error)
  }
)

export default api
