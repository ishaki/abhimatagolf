import { useAuthStore } from '@/store/auth'

/**
 * Centralized authentication error handler
 * This function should be called by API interceptors when a 401 error occurs
 */
export const handleAuthError = () => {
  const { logoutFromExternalSource } = useAuthStore.getState()
  logoutFromExternalSource()
}

/**
 * Check if an error is an authentication error (401)
 */
export const isAuthError = (error: any): boolean => {
  return error?.response?.status === 401
}

/**
 * Handle API errors and redirect to login if authentication fails
 */
export const handleApiError = (error: any) => {
  if (isAuthError(error)) {
    handleAuthError()
    return true // Indicates that the error was handled
  }
  return false // Error was not handled
}
