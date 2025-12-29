import { useEffect, useState, useRef } from 'react';
import { startSession, endSession } from './apiClient';

interface LocationInfo {
  latitude: number;
  longitude: number;
  accuracy?: number;
}

interface SessionOptions {
  userId: string;
  sessionId?: string;  // Optional: use existing session ID
  modelGroup: string;
  experimentId?: string;
  location?: LocationInfo | null;
  locationReady?: boolean;
}

/**
 * Hook to manage user session lifecycle
 * - Uses provided session ID or generates one
 * - Captures environment details
 * - Starts session on mount
 * - Ends session on unmount
 */
export function useSession({
  userId,
  sessionId: providedSessionId,
  modelGroup,
  experimentId,
  location,
  locationReady = true,
}: SessionOptions) {
  const [sessionId, setSessionId] = useState<string>('');
  const sessionStartedRef = useRef(false);

  useEffect(() => {
    // Don't create session if we don't have real userId or sessionId yet
    if (!locationReady || !experimentId) {
      return;
    }

    if (!userId || userId === 'anonymous' || !providedSessionId) {
      return;
    }

    if (sessionStartedRef.current) {
      return;
    }

    sessionStartedRef.current = true;

    const newSessionId = providedSessionId;
    setSessionId(newSessionId);

    // Capture environment details
    const environment = {
      device: getDeviceType(),
      browser: getBrowser(),
      os: getOS(),
      viewport: {
        width: window.innerWidth,
        height: window.innerHeight,
      },
      language: navigator.language || 'en',
      connection: getConnectionType(),
      location: location
        ? {
          latitude: location.latitude,
          longitude: location.longitude,
          accuracy: location.accuracy,
        }
        : undefined,
    };

    // Initialize session (backend will check if it exists)
    const initSession = async () => {
      try {
        const data = await startSession({
          session_id: newSessionId,
          user_id: userId,
          experiment_id: experimentId,
          environment,
        });

        if (data.status === 'exists') {
          console.log('✅ Session already exists:', newSessionId);
        } else {
          console.log('✅ New session created:', newSessionId);
        }
      } catch (error) {
        console.error('Failed to initialize session:', error);
      }
    };

    initSession();

    // End session on unmount or page unload
    const endSessionHandler = () => {
      // Use sendBeacon for reliable cleanup on page unload
      // Note: sendBeacon doesn't work well with apiClient, use direct fetch
      const backendUrl = (process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000').replace(/\/$/, '');
      const data = JSON.stringify({ session_id: newSessionId });
      const blob = new Blob([data], { type: 'application/json' });
      navigator.sendBeacon(`${backendUrl}/api/v1/session/end`, blob);
    };

    window.addEventListener('beforeunload', endSessionHandler);

    return () => {
      sessionStartedRef.current = false;
      window.removeEventListener('beforeunload', endSessionHandler);
      endSessionHandler();
    };
  }, [
    userId,
    providedSessionId,
    modelGroup,
    experimentId,
    locationReady,
    location?.latitude,
    location?.longitude,
    location?.accuracy,
  ]);

  return sessionId;
}

// Helper functions to detect environment details

function getDeviceType(): string {
  const ua = navigator.userAgent;
  if (/(tablet|ipad|playbook|silk)|(android(?!.*mobi))/i.test(ua)) {
    return 'tablet';
  }
  if (/Mobile|Android|iP(hone|od)|IEMobile|BlackBerry|Kindle|Silk-Accelerated|(hpw|web)OS|Opera M(obi|ini)/.test(ua)) {
    return 'mobile';
  }
  return 'desktop';
}

function getBrowser(): string {
  const ua = navigator.userAgent;
  if (ua.includes('Firefox/')) return 'Firefox';
  if (ua.includes('Edg/')) return 'Edge';
  if (ua.includes('Chrome/')) return 'Chrome';
  if (ua.includes('Safari/')) return 'Safari';
  if (ua.includes('Opera/') || ua.includes('OPR/')) return 'Opera';
  return 'Unknown';
}

function getOS(): string {
  const ua = navigator.userAgent;
  if (ua.includes('Win')) return 'Windows';
  if (ua.includes('Mac')) return 'macOS';
  if (ua.includes('X11') || ua.includes('Linux')) return 'Linux';
  if (ua.includes('Android')) return 'Android';
  if (ua.includes('iOS') || ua.includes('iPhone') || ua.includes('iPad')) return 'iOS';
  return 'Unknown';
}

function getConnectionType(): string {
  // @ts-ignore - navigator.connection is not standard but widely supported
  const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
  if (connection) {
    return connection.effectiveType || 'unknown';
  }
  return 'unknown';
}
