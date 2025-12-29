"use client";

import { useEffect, useRef } from "react";

interface EventTrackerProps {
  userId: string;
  sessionId: string;
}

export default function EventTracker({ userId, sessionId }: EventTrackerProps) {
  const scrollTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const lastScrollPositionRef = useRef(0);

  useEffect(() => {
    if (!userId || !sessionId) return;

    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

    // Track scroll events
    const handleScroll = () => {
      // Clear existing timeout
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }

      // Set new timeout to log scroll after user stops scrolling
      scrollTimeoutRef.current = setTimeout(async () => {
        const scrollPosition = window.scrollY;
        const scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
        const scrollDepth = scrollHeight > 0 ? scrollPosition / scrollHeight : 0;

        // Only log if scroll position changed significantly
        if (Math.abs(scrollPosition - lastScrollPositionRef.current) > 100) {
          lastScrollPositionRef.current = scrollPosition;

          try {
            await fetch(`${backendUrl}/log_event`, {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
              },
              body: JSON.stringify({
                user_id: userId,
                session_id: sessionId,
                event_type: "scroll",
                page_url: window.location.href,
                extra_data: {
                  scroll_position: scrollPosition,
                  scroll_depth: scrollDepth,
                },
              }),
            });
          } catch (err) {
            console.error("Error logging scroll event:", err);
          }
        }
      }, 500); // Wait 500ms after user stops scrolling
    };

    // Add event listeners
    window.addEventListener("scroll", handleScroll, { passive: true });

    // Cleanup
    return () => {
      window.removeEventListener("scroll", handleScroll);
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
    };
  }, [userId, sessionId]);

  // This component doesn't render anything visible
  return null;
}
