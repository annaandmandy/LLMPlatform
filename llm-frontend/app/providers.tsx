"use client";

import { useEffect } from "react";
import Clarity from "@microsoft/clarity";

const projectId = process.env.NEXT_PUBLIC_CLARITY_ID;

export default function AnalyticsProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    if (projectId) Clarity.init(projectId);
  }, []);
  return <>{children}</>;
}