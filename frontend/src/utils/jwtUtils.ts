/**
 * JWT Token Utilities
 *
 * Utilities for decoding and checking JWT token expiry.
 * Helps implement proactive token refresh to prevent session expiration errors.
 */

interface JWTPayload {
  sub: string;      // User ID
  email: string;
  role: string;
  exp: number;      // Expiration timestamp (seconds since epoch)
  iat?: number;     // Issued at timestamp
}

/**
 * Decode JWT token without verification
 * Note: This does NOT verify the token signature, only decodes the payload
 */
export const decodeJWT = (token: string): JWTPayload | null => {
  try {
    // JWT format: header.payload.signature
    const parts = token.split('.');
    if (parts.length !== 3) {
      console.error('Invalid JWT format');
      return null;
    }

    // Decode base64url payload (second part)
    const payload = parts[1];
    const base64 = payload.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );

    return JSON.parse(jsonPayload);
  } catch (error) {
    console.error('Failed to decode JWT:', error);
    return null;
  }
};

/**
 * Check if token is expired
 */
export const isTokenExpired = (token: string): boolean => {
  const payload = decodeJWT(token);
  if (!payload || !payload.exp) {
    return true; // Treat invalid tokens as expired
  }

  const currentTime = Math.floor(Date.now() / 1000); // Current time in seconds
  return currentTime >= payload.exp;
};

/**
 * Get token expiry time in seconds
 * Returns null if token is invalid
 */
export const getTokenExpiryTime = (token: string): number | null => {
  const payload = decodeJWT(token);
  return payload?.exp ?? null;
};

/**
 * Get remaining time until token expires (in seconds)
 * Returns 0 if token is expired or invalid
 */
export const getTokenRemainingTime = (token: string): number => {
  const expiryTime = getTokenExpiryTime(token);
  if (!expiryTime) {
    return 0;
  }

  const currentTime = Math.floor(Date.now() / 1000);
  const remaining = expiryTime - currentTime;
  return Math.max(0, remaining);
};

/**
 * Check if token will expire soon (within threshold)
 * Default threshold: 5 minutes (300 seconds)
 */
export const willTokenExpireSoon = (
  token: string,
  thresholdSeconds: number = 300
): boolean => {
  const remainingTime = getTokenRemainingTime(token);
  return remainingTime > 0 && remainingTime <= thresholdSeconds;
};

/**
 * Format remaining time as human-readable string
 * Example: "5 minutes", "30 seconds"
 */
export const formatRemainingTime = (seconds: number): string => {
  if (seconds <= 0) {
    return 'Expired';
  }

  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;

  if (minutes > 0) {
    return `${minutes} minute${minutes !== 1 ? 's' : ''}`;
  }

  return `${remainingSeconds} second${remainingSeconds !== 1 ? 's' : ''}`;
};

/**
 * Get token info for debugging
 */
export const getTokenInfo = (token: string): {
  valid: boolean;
  expired: boolean;
  expiresIn: string;
  payload: JWTPayload | null;
} => {
  const payload = decodeJWT(token);
  const expired = isTokenExpired(token);
  const remainingTime = getTokenRemainingTime(token);

  return {
    valid: payload !== null,
    expired,
    expiresIn: formatRemainingTime(remainingTime),
    payload,
  };
};
