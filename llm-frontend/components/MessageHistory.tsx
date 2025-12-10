"use client";

import React, { useState, CSSProperties, useEffect } from "react";
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
  attachments?: { type: string; base64?: string; name?: string }[];
  options?: string[];
}

interface MessageHistoryProps {
  messages: Message[];
  userId: string;
  sessionId: string;
  messagesEndRef: React.RefObject<HTMLDivElement>;
  isLoading?: boolean;
  thinkingText?: string;
  onOptionSelect?: (option: string) => void;
}

function normalizeMarkdown(text: string) {
  // Ensure proper spacing before list items for markdown parsing
  // Also handle cases where list items might be split incorrectly
  return text
    .replace(/([^\n])\n-/g, "$1\n\n-")  // Add blank line before dash lists
    .replace(/([^\n])\n\*/g, "$1\n\n*")  // Add blank line before asterisk lists
    .replace(/([^\n])\n(\d+\.)/g, "$1\n\n$2");  // Add blank line before numbered lists
}

export default function MessageHistory({
  messages,
  userId,
  sessionId,
  messagesEndRef,
  isLoading = false,
  thinkingText = "",
  onOptionSelect,
}: MessageHistoryProps) {
  const [clickedLinks, setClickedLinks] = useState<Set<string>>(new Set());
  const [expandedSources, setExpandedSources] = useState<Set<number>>(new Set());
  const typingDotStyle = (delay: number): CSSProperties => ({ animationDelay: `${delay}s` });

  // Scroll to bottom when loading state changes
  useEffect(() => {
    if (messagesEndRef?.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [isLoading]);

  useEffect(() => {
    if (messagesEndRef?.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages.length]);

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
              className={`${isClicked ? "text-indigo-600" : "text-blue-700"
                } hover:text-blue-800 underline`}
            >
              {children}
            </a>
          );
        },
        h1: ({ children }) => (
          <h1 className="text-2xl font-semibold mt-4 mb-2 text-slate-900">
            {children}
          </h1>
        ),
        h2: ({ children }) => (
          <h2 className="text-xl font-semibold mt-4 mb-2 text-slate-900">
            {children}
          </h2>
        ),
        h3: ({ children }) => (
          <h3 className="text-lg font-semibold mt-3 mb-1.5 text-slate-900">
            {children}
          </h3>
        ),
        ul: ({ children }) => (
          <ul className="list-disc ml-6 my-2 space-y-0.5 text-base text-slate-800 [&>li>p]:inline [&>li>p]:m-0">
            {children}
          </ul>
        ),
        ol: ({ children }) => (
          <ol className="list-decimal ml-6 my-2 space-y-0.5 text-base text-slate-800 [&>li>p]:inline [&>li>p]:m-0">
            {children}
          </ol>
        ),
        li: ({ children }) => (
          <li className="leading-relaxed">{children}</li>
        ),
        p: ({ children }) => (
          <p className="mb-3 leading-relaxed text-base text-slate-800">
            {children}
          </p>
        ),
        strong: ({ children }) => (
          <strong className="font-semibold">{children}</strong>
        ),
        code: ({ children }) => (
          <code className="px-1.5 py-0.5 bg-slate-100 text-slate-800 rounded text-sm font-mono">
            {children}
          </code>
        ),
        pre: ({ children }) => (
          <pre className="bg-slate-900 text-slate-100 p-4 rounded-xl overflow-x-auto text-sm font-mono my-3">
            {children}
          </pre>
        ),
        img: ({ src, alt }) => (
          <img
            src={src || ""}
            alt={alt || ""}
            className="max-w-full rounded-lg border border-slate-200 my-3"
          />
        ),
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
            className={`flex ${message.role === "user" ? "justify-end" : "justify-start"
              }`}
          >
            <div
              className={`${message.role === "user" ? "max-w-[75%] ml-auto" : "w-full"
                } flex flex-col gap-3`}
            >
              {/* Message Bubble */}
              <div
                className={
                  message.role === "user"
                    ? "max-w-[85%] ml-auto px-4 py-2.5 rounded-2xl bg-white border border-slate-200 shadow-sm text-slate-900 mb-3"
                    : "bg-transparent text-gray-800"
                }
              >
                <div className="max-w-none">
                  {message.role === "assistant"
                    ? renderMarkdown(normalizeMarkdown(message.content), queryContext)
                    : message.content}
                </div>
                {/* Attachments */}
                {message.attachments && message.attachments.length > 0 && (
                  <div className="mt-3 grid grid-cols-3 gap-2">
                    {message.attachments
                      .filter((a) => a.type === "image" && a.base64)
                      .map((a, idx) => (
                        <img
                          key={idx}
                          src={a.base64}
                          alt={a.name || "attachment"}
                          className="w-full h-24 object-cover rounded-md border border-gray-200"
                        />
                      ))}
                  </div>
                )}

                {/* Options Buttons */}
                {message.role === "assistant" && message.options && message.options.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {message.options.map((option, idx) => (
                      <button
                        key={idx}
                        onClick={() => onOptionSelect && onOptionSelect(option)}
                        className="px-4 py-2 bg-blue-50 text-blue-700 text-sm font-medium rounded-full border border-blue-200 hover:bg-blue-100 hover:border-blue-300 transition-colors text-left"
                      >
                        {option}
                      </button>
                    ))}
                  </div>
                )}

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
                  className={`text-xs mt-2 ${message.role === "user" ? "text-blue-100" : "text-gray-400"
                    }`}
                >
                  {message.timestamp.toLocaleTimeString()}
                </div>
              </div>

              {/* Product Cards - Show for each message that has them */}
              {message.role === "assistant" && message.product_cards && message.product_cards.length > 0 && (
                <div className="w-full">
                  <div className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                    <span>🛍️</span>
                    <span>Related Products</span>
                  </div>
                  <div className="overflow-x-auto">
                    <div className="flex gap-3 pb-2">
                      {message.product_cards.map((product, idx) => (
                        <ProductCard key={idx} {...product} />
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        );
      })}

      {isLoading && (
        <div className="flex justify-start">
          <div className="max-w-[85%] w-full">
            {thinkingText ? (
              <div className="flex items-center gap-2 text-slate-600 text-sm whitespace-nowrap overflow-hidden">
                {thinkingText.startsWith("Searching for products:") ? (
                  <>
                    <svg className="w-3.5 h-3.5 text-blue-600 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                    <span className="text-slate-500 shrink-0">Searching for</span>
                    <span className="font-medium text-slate-700 overflow-hidden text-ellipsis">
                      {thinkingText.replace("Searching for products: ", "")}
                    </span>
                  </>
                ) : (
                  <>
                    <svg className="w-3.5 h-3.5 text-slate-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                    </svg>
                    <span className="text-slate-700 overflow-hidden text-ellipsis">{thinkingText}</span>
                  </>
                )}
                <span className="shrink-0 flex items-center gap-1 ml-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce" />
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce" style={typingDotStyle(0.15)} />
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce" style={typingDotStyle(0.3)} />
                </span>
              </div>
            ) : (
              <div className="flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce" />
                <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce" style={typingDotStyle(0.15)} />
                <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce" style={typingDotStyle(0.3)} />
              </div>
            )}
          </div>
        </div>
      )}
      <div ref={messagesEndRef} />
    </div>
  );
}
