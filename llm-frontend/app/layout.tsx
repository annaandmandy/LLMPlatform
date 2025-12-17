import type { Metadata } from "next";
import Script from "next/script";
import "./globals.css";
import { Analytics } from "@vercel/analytics/next";
import AnalyticsProvider from "./providers";
import { SpeedInsights } from "@vercel/speed-insights/next";


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
    <html lang="en" suppressHydrationWarning>
      <body>
        <AnalyticsProvider>
          <Script
            src="https://www.googletagmanager.com/gtag/js?id=G-0SQLMR12QD"
            strategy="afterInteractive"
          />
          <Script id="ga-gtag" strategy="afterInteractive">
            {`
              window.dataLayer = window.dataLayer || [];
              function gtag(){dataLayer.push(arguments);}
              gtag('js', new Date());
              gtag('config', 'G-0SQLMR12QD');
            `}
          </Script>
          <Script
            id="contentsquare"
            src="https://t.contentsquare.net/uxa/ae3be3e62b061.js"
            strategy="afterInteractive"
          />
          <Analytics />
          <SpeedInsights />
          {children}
        </AnalyticsProvider>
      </body>
    </html>
  );
}
