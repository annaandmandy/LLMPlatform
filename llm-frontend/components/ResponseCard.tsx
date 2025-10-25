"use client";

import { useState } from "react";

interface ResponseCardProps {
  response: string;
  query: string;
  userId: string;
  sessionId: string;
}

export default function ResponseCard({
  response,
  query,
  userId,
  sessionId,
}: ResponseCardProps) {
  const [clickedLinks, setClickedLinks] = useState<Set<string>>(new Set());

  const handleLinkClick = async (href: string) => {
    // Log click event
    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

      await fetch(`${backendUrl}/log_event`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_id: userId,
          session_id: sessionId,
          event_type: "click",
          query: query,
          target_url: href,
          page_url: window.location.href,
        }),
      });

      setClickedLinks(new Set([...clickedLinks, href]));
    } catch (err) {
      console.error("Error logging click event:", err);
    }
  };

  // Parse response to detect and make URLs clickable
  const renderResponseWithLinks = (text: string) => {
    const urlRegex = /(https?:\/\/[^\s]+)/g;
    const parts = text.split(urlRegex);

    return parts.map((part, index) => {
      if (part.match(urlRegex)) {
        const isClicked = clickedLinks.has(part);
        return (
          <a
            key={index}
            href={part}
            target="_blank"
            rel="noopener noreferrer"
            onClick={() => handleLinkClick(part)}
            className={`${
              isClicked ? "text-purple-600" : "text-blue-600"
            } hover:text-blue-800 underline break-all`}
          >
            {part}
          </a>
        );
      }
      return <span key={index}>{part}</span>;
    });
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 animate-fade-in">
      <h2 className="text-xl font-semibold text-gray-800 mb-4">Response</h2>
      <div className="prose max-w-none">
        <div className="text-gray-700 whitespace-pre-wrap leading-relaxed">
          {renderResponseWithLinks(response)}
        </div>
      </div>

      <div className="mt-6 pt-4 border-t border-gray-200">
        <p className="text-sm text-gray-500">
          Click on any links in the response to explore more. All interactions are logged for analysis.
        </p>
      </div>
    </div>
  );
}
