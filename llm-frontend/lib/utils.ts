/**
 * Utility functions for the LLM frontend application
 */

/**
 * Generate a unique user ID
 */
export function generateUserId(): string {
  return crypto.randomUUID();
}

/**
 * Get or create user ID from localStorage
 */
export function getUserId(): string {
  if (typeof window === "undefined") return "";

  let userId = localStorage.getItem("user_id");
  if (!userId) {
    userId = generateUserId();
    localStorage.setItem("user_id", userId);
  }
  return userId;
}

/**
 * Get or create session ID from sessionStorage
 */
export function getSessionId(): string {
  if (typeof window === "undefined") return "";

  let sessionId = sessionStorage.getItem("session_id");
  if (!sessionId) {
    sessionId = generateUserId();
    sessionStorage.setItem("session_id", sessionId);
  }
  return sessionId;
}

/**
 * Format timestamp to readable string
 */
export function formatTimestamp(timestamp: string | Date): string {
  const date = typeof timestamp === "string" ? new Date(timestamp) : timestamp;
  return date.toLocaleString();
}

/**
 * Validate URL format
 */
export function isValidUrl(url: string): boolean {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}
