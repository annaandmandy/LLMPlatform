"use client";

import { useEffect } from "react";
import Clarity from "@microsoft/clarity";

const projectId = process.env.NEXT_PUBLIC_CLARITY_ID;

export default function AnalyticsProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    if (projectId) {
      // Wait for DOM to be fully ready including all stylesheets
      if (document.readyState === 'complete') {
        Clarity.init(projectId);
      } else {
        window.addEventListener('load', () => {
          Clarity.init(projectId);
        });
      }

      // Optional: Add custom tracking events
      // Example: Clarity.identify(userId, sessionId, pageId, friendlyName);
      // Example: Clarity.setTag("user_type", "premium");
    }
  }, []);

  return <>{children}</>;
}