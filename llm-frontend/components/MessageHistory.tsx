"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import ProductCard from "./ProductCard";

interface Citation {
  title: string;
  url: string;
}

interface ProductCardData {
  title: string;
  description?: string;
  price?: string;
  rating?: number;
  reviews_count?: number;
  image?: string;
  url: string;
  seller?: string;
  tag?: string;
  delivery?: string;
}

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  citations?: Citation[];
  product_cards?: ProductCardData[];
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
    try {
      const backendUrl =
        process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

      await fetch(`${backendUrl}/log_event`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          session_id: sessionId,
          event_type: "click",
          query,
          target_url: href,
          page_url: window.location.href,
        }),
      });

      setClickedLinks(new Set([...clickedLinks, href]));
    } catch (err) {
      console.error("Error logging click event:", err);
    }
  };

  // Use react-markdown to render assistant replies
  const renderMarkdown = (text: string, query: string) => (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        a: ({ href, children }) => {
          const link = href || "#";
          const isClicked = clickedLinks.has(link);
          return (
            <a
              href={link}
              target="_blank"
              rel="noopener noreferrer"
              onClick={() => handleLinkClick(link, query)}
              className={`${
                isClicked ? "text-purple-600" : "text-blue-600"
              } hover:text-blue-800 underline`}
            >
              {children}
            </a>
          );
        },
        h1: ({ children }) => (
          <h1 className="text-xl font-bold mt-2 mb-1">{children}</h1>
        ),
        h2: ({ children }) => (
          <h2 className="text-lg font-semibold mt-2 mb-1">{children}</h2>
        ),
        h3: ({ children }) => (
          <h3 className="text-md font-medium mt-2 mb-1">{children}</h3>
        ),
        ul: ({ children }) => <ul className="list-disc ml-5 space-y-1">{children}</ul>,
        ol: ({ children }) => <ol className="list-decimal ml-5 space-y-1">{children}</ol>,
        li: ({ children }) => <li className="leading-snug">{children}</li>,
        p: ({ children }) => <p className="mb-2 leading-relaxed">{children}</p>,
      }}
    >
      {text}
    </ReactMarkdown>
  );

  if (messages.length === 0) {
    return (
      <div className="p-8 flex items-center justify-center min-h-[400px]">
        <div className="text-center text-gray-500">
          <p className="text-lg mb-2">No messages yet</p>
          <p className="text-sm">
            Start a conversation by typing a query below
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-4">
      {messages.map((message, index) => {
        const queryContext =
          message.role === "user"
            ? message.content
            : index > 0 && messages[index - 1].role === "user"
            ? messages[index - 1].content
            : "";

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
              <div className="prose prose-sm max-w-none">
                {message.role === "assistant"
                  ? renderMarkdown(message.content, queryContext)
                  : message.content}
              </div>

              {/* ✅ TOGGLEABLE CITATIONS */}
              {message.role === "assistant" &&
                message.citations &&
                message.citations.length > 0 && (
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
                              onClick={() =>
                                handleLinkClick(src.url, queryContext)
                              }
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

            {/* Product Cards - Show for each message that has them */}
            {message.role === "assistant" && message.product_cards && message.product_cards.length > 0 && (
              <div className="mt-3 max-w-[80%]">
                <div className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                  <span>🛍️</span>
                  <span>Related Products</span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {message.product_cards.map((product, idx) => (
                    <ProductCard key={idx} {...product} />
                  ))}
                </div>
              </div>
            )}
          </div>
        );
      })}

      <div ref={messagesEndRef} />
    </div>
  );
}
