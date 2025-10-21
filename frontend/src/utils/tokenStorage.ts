/**
 * Token storage utilities for authentication
 */

export const TOKEN_KEYS = {
  ACCESS_TOKEN: 'access_token',
  REFRESH_TOKEN: 'refresh_token',
  USER_DATA: 'user_data'
} as const

export const tokenStorage = {
  // Access token
  getAccessToken: (): string | null => {
    return localStorage.getItem(TOKEN_KEYS.ACCESS_TOKEN)
  },

  setAccessToken: (token: string): void => {
    localStorage.setItem(TOKEN_KEYS.ACCESS_TOKEN, token)
  },

  removeAccessToken: (): void => {
    localStorage.removeItem(TOKEN_KEYS.ACCESS_TOKEN)
  },

  // Refresh token
  getRefreshToken: (): string | null => {
    return localStorage.getItem(TOKEN_KEYS.REFRESH_TOKEN)
  },

  setRefreshToken: (token: string): void => {
    localStorage.setItem(TOKEN_KEYS.REFRESH_TOKEN, token)
  },

  removeRefreshToken: (): void => {
    localStorage.removeItem(TOKEN_KEYS.REFRESH_TOKEN)
  },

  // User data
  getUserData: (): any | null => {
    const userData = localStorage.getItem(TOKEN_KEYS.USER_DATA)
    return userData ? JSON.parse(userData) : null
  },

  setUserData: (userData: any): void => {
    localStorage.setItem(TOKEN_KEYS.USER_DATA, JSON.stringify(userData))
  },

  removeUserData: (): void => {
    localStorage.removeItem(TOKEN_KEYS.USER_DATA)
  },

  // Clear all tokens
  clearAll: (): void => {
    localStorage.removeItem(TOKEN_KEYS.ACCESS_TOKEN)
    localStorage.removeItem(TOKEN_KEYS.REFRESH_TOKEN)
    localStorage.removeItem(TOKEN_KEYS.USER_DATA)
  },

  // Check if user is authenticated
  isAuthenticated: (): boolean => {
    const accessToken = tokenStorage.getAccessToken()
    if (!accessToken) return false

    try {
      // Check if token is expired
      const payload = JSON.parse(atob(accessToken.split('.')[1]))
      const currentTime = Date.now() / 1000
      return payload.exp > currentTime
    } catch {
      return false
    }
  }
}
