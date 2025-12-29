import { useEffect, useCallback, useRef } from 'react';

interface EventData {
  text?: string;
  target?: string;
  target_url?: string;  // URL for link clicks
  x?: number;
  y?: number;
  scrollY?: number;
  speed?: number;
  direction?: 'up' | 'down';
  model?: string;
  provider?: string;
  latency_ms?: number;
  feedback?: 'up' | 'down' | 'neutral';
  selected_text?: string;
  page_url?: string;
  [key: string]: any;
}

interface EventTrackingOptions {
  sessionId: string;
  trackScroll?: boolean;
  trackClicks?: boolean;
  trackHover?: boolean;
  trackSelection?: boolean;
  trackActivity?: boolean;
  trackZoom?: boolean;
  scrollThrottle?: number; // ms between scroll events
  activityIdleTimeout?: number; // ms before considering user idle
}

/**
 * Hook to track user interactions and log them to the session
 * - Tracks scroll, click, hover, selection events
 * - Tracks user activity/idle state
 * - Provides a generic logEvent function for custom events
 */
export function useEventTracking({
  sessionId,
  trackScroll = true,
  trackClicks = true,
  trackHover = false,
  trackSelection = true,
  trackActivity = true,
  trackZoom = true,
  scrollThrottle = 500,
  activityIdleTimeout = 30000, // 30 seconds
}: EventTrackingOptions) {
  const lastScrollY = useRef(typeof window !== 'undefined' ? window.scrollY : 0);
  const lastScrollTime = useRef(Date.now());
  const scrollTimeout = useRef<NodeJS.Timeout>();
  const activityTimeout = useRef<NodeJS.Timeout>();
  const isIdle = useRef(false);
  const lastSelection = useRef<string>('');
  const selectionTimeout = useRef<NodeJS.Timeout>();
  const lastHoveredElement = useRef<string>('');
  const lastZoomLevel = useRef(typeof window !== 'undefined' ? window.visualViewport?.scale || 1 : 1);

  /**
   * Generic event logging function
   */
  const logEvent = useCallback(async (type: string, data: EventData = {}) => {
    if (!sessionId) return;

    try {
      const backendUrl = (process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000').replace(/\/$/, '');
      await fetch(`${backendUrl}/api/v1/session/event`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          event: {
            t: Date.now(),
            type,
            data,
          },
        }),
      });
    } catch (error) {
      console.error('Failed to log event:', error);
    }
  }, [sessionId]);

  /**
   * Mark user as active and reset idle timer
   */
  const markActive = useCallback(() => {
    // Just reset idle state without logging events
    if (isIdle.current) {
      isIdle.current = false;
    }

    // Reset idle timeout
    if (activityTimeout.current) {
      clearTimeout(activityTimeout.current);
    }

    activityTimeout.current = setTimeout(() => {
      isIdle.current = true;
    }, activityIdleTimeout);
  }, [activityIdleTimeout]);

  useEffect(() => {
    if (!sessionId) return;

    // Track scrolling with throttling
    const handleScroll = () => {
      if (!trackScroll) return;

      markActive();

      const currentScrollY = window.scrollY;
      const currentTime = Date.now();

      // Throttle scroll events
      if (scrollTimeout.current) {
        clearTimeout(scrollTimeout.current);
      }

      scrollTimeout.current = setTimeout(() => {
        const timeDiff = currentTime - lastScrollTime.current;
        const scrollDiff = currentScrollY - lastScrollY.current;

        if (timeDiff > 0) {
          logEvent('scroll', {
            scrollY: currentScrollY,
            speed: Math.abs(scrollDiff / timeDiff) * 1000, // pixels per second
            direction: scrollDiff > 0 ? 'down' : 'up',
          });
        }

        lastScrollY.current = currentScrollY;
        lastScrollTime.current = currentTime;
      }, scrollThrottle);
    };

    // Track clicks
    const handleClick = (e: MouseEvent) => {
      if (!trackClicks) return;

      markActive();

      const target = e.target as HTMLElement;

      // Capture text content BEFORE any DOM updates (during capture phase)
      // This ensures we get the original text before state changes
      const originalText = target.textContent?.trim() || undefined;

      const eventData: EventData = {
        target: target.tagName,
        x: e.clientX,
        y: e.clientY,
      };

      // If clicking on a link or inside a link, capture the URL
      let linkElement = target.closest('a');
      if (linkElement && linkElement.href) {
        eventData.target_url = linkElement.href;
        eventData.text = linkElement.textContent?.trim() || undefined;
      }

      // If clicking on a button with data attributes or specific info
      if (target.tagName === 'BUTTON') {
        eventData.text = originalText;
      }

      logEvent('click', eventData);
    };

    // Track hover (mouseover on interactive elements) with throttling
    const handleHover = (e: MouseEvent) => {
      if (!trackHover) return;

      const target = e.target as HTMLElement;
      const trackedElement = target.closest<HTMLElement>('[data-hover-id]') || target.closest('a, button');

      if (!trackedElement) return;

      const hoverId =
        trackedElement.getAttribute('data-hover-id') ||
        `${trackedElement.tagName}:${trackedElement.textContent?.trim().substring(0, 50) || ''}`;

      if (lastHoveredElement.current === hoverId) return;
      lastHoveredElement.current = hoverId;

      const linkElement = trackedElement.closest('a');
      logEvent('hover', {
        target: trackedElement.tagName,
        text: trackedElement.textContent?.trim().substring(0, 100) || undefined,
        target_url: linkElement ? linkElement.href : undefined,
        x: e.clientX,
        y: e.clientY,
      });
    };

    // Track text selection (debounced to only capture final selection)
    const handleSelection = () => {
      if (!trackSelection) return;

      // Clear previous timeout
      if (selectionTimeout.current) {
        clearTimeout(selectionTimeout.current);
      }

      // Wait for user to finish selecting (300ms debounce)
      selectionTimeout.current = setTimeout(() => {
        const selection = window.getSelection();
        const selectedText = selection?.toString().trim() || '';

        // Only log if:
        // 1. There's actual text selected (length > 0)
        // 2. It's different from the last selection (avoid duplicates)
        // 3. It's more than just a single character (intentional selection)
        if (selectedText.length > 1 && selectedText !== lastSelection.current) {
          markActive();

          lastSelection.current = selectedText;

          logEvent('selection', {
            selected_text: selectedText.substring(0, 500), // Limit to 500 chars
            page_url: window.location.pathname,
          });
        }
      }, 300); // 300ms debounce
    };

    // Track copy events
    const handleCopy = () => {
      markActive();

      const selection = window.getSelection();
      const selectedText = selection?.toString().trim() || '';

      if (selectedText.length > 0) {
        logEvent('copy', {
          selected_text: selectedText.substring(0, 500),
          page_url: window.location.pathname,
        });
      }
    };

    // Track navigation
    const handleNavigation = () => {
      logEvent('navigate', {
        page_url: window.location.pathname,
      });
    };

    // Track keyboard interactions
    const handleKeyPress = (e: KeyboardEvent) => {
      markActive();

      // Only track special keys (not every keystroke for privacy)
      if (['Enter', 'Escape', 'Tab'].includes(e.key)) {
        logEvent('key', {
          target: e.key,
        });
      }
    };

    // Track zoom/pinch events
    const handleZoom = () => {
      if (!trackZoom) return;
      if (typeof window === 'undefined' || !window.visualViewport) return;

      const currentZoom = window.visualViewport.scale;

      // Only log if zoom level changed significantly (more than 0.05 difference)
      if (Math.abs(currentZoom - lastZoomLevel.current) > 0.05) {
        markActive();

        logEvent('zoom', {
          zoom_level: currentZoom,
          previous_zoom: lastZoomLevel.current,
          viewport_width: window.visualViewport.width,
          viewport_height: window.visualViewport.height,
        });

        lastZoomLevel.current = currentZoom;
      }
    };

    // Add event listeners
    if (trackScroll) {
      window.addEventListener('scroll', handleScroll, { passive: true });
    }
    if (trackClicks) {
      // Use capture phase to get original text before React updates
      window.addEventListener('click', handleClick, true);
    }
    if (trackHover) {
      window.addEventListener('mouseover', handleHover, { passive: true });
    }
    if (trackSelection) {
      document.addEventListener('selectionchange', handleSelection);
    }
    if (trackZoom && typeof window !== 'undefined' && window.visualViewport) {
      window.visualViewport.addEventListener('resize', handleZoom);
    }
    document.addEventListener('copy', handleCopy);
    window.addEventListener('popstate', handleNavigation);
    document.addEventListener('keydown', handleKeyPress);

    // Cleanup
    return () => {
      window.removeEventListener('scroll', handleScroll);
      window.removeEventListener('click', handleClick, true);
      window.removeEventListener('mouseover', handleHover);
      document.removeEventListener('selectionchange', handleSelection);
      if (typeof window !== 'undefined' && window.visualViewport) {
        window.visualViewport.removeEventListener('resize', handleZoom);
      }
      document.removeEventListener('copy', handleCopy);
      window.removeEventListener('popstate', handleNavigation);
      document.removeEventListener('keydown', handleKeyPress);

      if (scrollTimeout.current) {
        clearTimeout(scrollTimeout.current);
      }
      if (activityTimeout.current) {
        clearTimeout(activityTimeout.current);
      }
      if (selectionTimeout.current) {
        clearTimeout(selectionTimeout.current);
      }
    };
  }, [sessionId, trackScroll, trackClicks, trackHover, trackSelection, trackActivity, trackZoom, logEvent, markActive, scrollThrottle]);

  return { logEvent };
}
