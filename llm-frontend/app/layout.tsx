import type { Metadata } from "next";
import "./globals.css";

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
      <body>{children}</body>
    </html>
  );
}
