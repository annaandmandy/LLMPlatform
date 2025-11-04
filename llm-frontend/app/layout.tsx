import type { Metadata } from "next";
import Script from "next/script";
import "./globals.css";
import { Analytics } from "@vercel/analytics/next"
import AnalyticsProvider from "./providers";
import { SpeedInsights } from "@vercel/speed-insights/next"


export const metadata: Metadata = {
  title: "LLM Brand Experiment",
  description: "Interactive LLM brand exploration platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <AnalyticsProvider>
            <Analytics />
            <SpeedInsights/>
            {children}
        </AnalyticsProvider>
      </body>
    </html>
  );
}
