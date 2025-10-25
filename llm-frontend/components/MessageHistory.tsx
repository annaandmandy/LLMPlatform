"use client";

import { useState } from "react";

interface Citation {
  title: string;
  url: string;
}

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  citations?: Citation[]
}

interface MessageHistoryProps {
  messages: Message[];
  userId: string;
  sessionId: string;
  messagesEndRef: React.RefObject<HTMLDivElement>;
}

export default function MessageHistory({
  messages,
  userId,
  sessionId,
  messagesEndRef,
}: MessageHistoryProps) {
  const [clickedLinks, setClickedLinks] = useState<Set<string>>(new Set());
  const [expandedSources, setExpandedSources] = useState<Set<number>>(new Set());

  const toggleSources = (index: number) => {
    const updated = new Set(expandedSources);
    updated.has(index) ? updated.delete(index) : updated.add(index);
    setExpandedSources(updated);
  };

  const handleLinkClick = async (href: string, query: string) => {
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
  const renderTextWithLinks = (text: string, query: string) => {
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
            onClick={() => handleLinkClick(part, query)}
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

  if (messages.length === 0) {
    return (
      <div className="flex-1 overflow-y-auto p-8 flex items-center justify-center">
        <div className="text-center text-gray-500">
          <p className="text-lg mb-2">No messages yet</p>
          <p className="text-sm">Start a conversation by typing a query below</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-4">
      {messages.map((message, index) => {
        // For user messages, use the message content as query context
        const queryContext = message.role === "user" ? message.content :
          (index > 0 && messages[index - 1].role === "user" ? messages[index - 1].content : "");

        const showSources = expandedSources.has(index);

        return (
          <div
            key={index}
            className={`flex ${
              message.role === "user" ? "justify-end" : "justify-start"
            }`}
          >
            <div
              className={`max-w-[80%] rounded-lg px-4 py-3 ${
                message.role === "user"
                  ? "bg-blue-600 text-white"
                  : "bg-white text-gray-800 shadow-md border border-gray-200"
              }`}
            >
              <div className="whitespace-pre-wrap break-words">
                {message.role === "assistant"
                  ? renderTextWithLinks(message.content, queryContext)
                  : message.content}
              </div>
              {/* ✅ TOGGLEABLE SOURCES SECTION */}
              {message.role === "assistant" && message.citations && message.citations.length > 0 && (
                <div className="mt-3 border-t border-gray-200 pt-2">
                  <button
                    onClick={() => toggleSources(index)}
                    className="text-blue-600 text-xs hover:underline flex items-center gap-1"
                  >
                    {showSources ? "Hide Sources ▲" : "Show Sources ▼"}
                  </button>

                  {showSources && (
                    <ul className="mt-2 space-y-1 text-xs text-gray-700">
                      {message.citations.map((src, sIdx) => (
                        <li key={sIdx}>
                          <a
                            href={src.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={() => handleLinkClick(src.url, queryContext)}
                            className="text-blue-600 hover:text-blue-800 underline break-all"
                          >
                            🔗 {src.title || src.url}
                          </a>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
              <div
                className={`text-xs mt-2 ${
                  message.role === "user" ? "text-blue-100" : "text-gray-400"
                }`}
              >
                {message.timestamp.toLocaleTimeString()}
              </div>
            </div>
          </div>
        );
      })}
      <div ref={messagesEndRef} />
    </div>
  );
}
