/**
 * Token Monitor
 *
 * Background service that periodically checks token expiry status
 * and warns users before their session expires.
 */

import { getTokenRemainingTime, formatRemainingTime } from './jwtUtils'
import { toast } from 'sonner'

class TokenMonitor {
  private intervalId: NodeJS.Timeout | null = null
  private lastWarningTime: number = 0
  private readonly CHECK_INTERVAL = 60000 // Check every 60 seconds
  private readonly WARNING_THRESHOLD = 300 // Warn when < 5 minutes remaining
  private readonly WARNING_COOLDOWN = 120000 // Only show warning every 2 minutes

  /**
   * Start monitoring token expiry
   */
  start() {
    // Clear any existing interval
    this.stop()

    // Start periodic checks
    this.intervalId = setInterval(() => {
      this.checkTokenStatus()
    }, this.CHECK_INTERVAL)

    // Run initial check
    this.checkTokenStatus()

    console.log('Token monitor started')
  }

  /**
   * Stop monitoring
   */
  stop() {
    if (this.intervalId) {
      clearInterval(this.intervalId)
      this.intervalId = null
      console.log('Token monitor stopped')
    }
  }

  /**
   * Check current token status and warn if needed
   */
  private checkTokenStatus() {
    const token = localStorage.getItem('access_token')

    if (!token) {
      // No token - user not logged in
      return
    }

    const remainingTime = getTokenRemainingTime(token)

    // Token expired
    if (remainingTime <= 0) {
      console.warn('Token has expired')
      return
    }

    // Token expiring soon - show warning
    if (remainingTime <= this.WARNING_THRESHOLD) {
      const now = Date.now()

      // Only show warning if enough time has passed since last warning
      if (now - this.lastWarningTime >= this.WARNING_COOLDOWN) {
        this.showExpiryWarning(remainingTime)
        this.lastWarningTime = now
      }
    }
  }

  /**
   * Show user-friendly warning about session expiry
   */
  private showExpiryWarning(remainingSeconds: number) {
    const timeLeft = formatRemainingTime(remainingSeconds)

    toast.warning('Session Expiring Soon', {
      description: `Your session will expire in ${timeLeft}. Activity will refresh your session automatically.`,
      duration: 10000,
    })

    console.warn(`Session expiring in ${timeLeft}`)
  }

  /**
   * Reset warning cooldown (call after successful refresh)
   */
  resetWarning() {
    this.lastWarningTime = 0
  }
}

// Create singleton instance
export const tokenMonitor = new TokenMonitor()

/**
 * Initialize token monitoring (call on app startup after login)
 */
export const startTokenMonitoring = () => {
  tokenMonitor.start()
}

/**
 * Stop token monitoring (call on logout)
 */
export const stopTokenMonitoring = () => {
  tokenMonitor.stop()
}
