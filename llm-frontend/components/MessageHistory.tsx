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
}

interface MessageHistoryProps {
  messages: Message[];
  userId: string;
  sessionId: string;
  messagesEndRef: React.RefObject<HTMLDivElement>;
  isLoading?: boolean;
  thinkingText?: string;
}

function normalizeMarkdown(text: string) {
  return text.replace(/([^\n])\n-/g, "$1\n\n-");
}

export default function MessageHistory({
  messages,
  userId,
  sessionId,
  messagesEndRef,
  isLoading = false,
  thinkingText = "",
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
              className={`${
                isClicked ? "text-indigo-600" : "text-blue-700"
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
          <ul className="list-disc ml-6 my-2 space-y-1.5 text-base text-slate-800">
            {children}
          </ul>
        ),
        ol: ({ children }) => (
          <ol className="list-decimal ml-6 my-2 space-y-1.5 text-base text-slate-800">
            {children}
          </ol>
        ),
        li: ({ children }) => <li className="leading-relaxed">{children}</li>,
        p: ({ children }) => (
          <p className="mb-3 leading-relaxed text-base text-slate-800 break-words">
            {children}
          </p>
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
            className={`flex ${
              message.role === "user" ? "justify-end" : "justify-start"
            }`}
          >
            <div
              className={`${
                message.role === "user" ? "max-w-[75%] ml-auto" : "w-full"
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
                <div className="prose prose-sm max-w-none">
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
            <div className="text-gray-600 text-sm leading-relaxed">
              {thinkingText ? (
                <div className="space-y-1">
                  {thinkingText.startsWith("Searching for products:") ? (
                    <>
                      <div className="flex items-center gap-2 text-blue-600">
                        <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
                        </svg>
                        <span className="font-medium">Searching Google Shopping...</span>
                      </div>
                      <div className="text-gray-500 text-xs pl-6">
                        {thinkingText.replace("Searching for products: ", "")}
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="flex items-center gap-2">
                        <span className="text-gray-500">Thinking about:</span>
                        <span className="text-gray-700 font-medium truncate max-w-md">{thinkingText}</span>
                      </div>
                      <div className="flex items-center gap-1.5 text-gray-400">
                        <span>Analyzing</span>
                        <span className="w-1.5 h-1.5 rounded-full bg-gray-400 animate-pulse" />
                        <span className="w-1.5 h-1.5 rounded-full bg-gray-400 animate-pulse" style={typingDotStyle(0.15)} />
                        <span className="w-1.5 h-1.5 rounded-full bg-gray-400 animate-pulse" style={typingDotStyle(0.3)} />
                      </div>
                    </>
                  )}
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <span className="text-gray-500">Processing</span>
                  <span className="w-1.5 h-1.5 rounded-full bg-gray-400 animate-pulse" />
                  <span className="w-1.5 h-1.5 rounded-full bg-gray-400 animate-pulse" style={typingDotStyle(0.15)} />
                  <span className="w-1.5 h-1.5 rounded-full bg-gray-400 animate-pulse" style={typingDotStyle(0.3)} />
                </div>
              )}
            </div>
          </div>
        </div>
      )}
      <div ref={messagesEndRef} />
    </div>
  );
}
