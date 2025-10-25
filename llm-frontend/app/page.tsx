"use client";

import { useState, useEffect, useRef } from "react";
import QueryBox from "@/components/QueryBox";
import MessageHistory from "@/components/MessageHistory";
import EventTracker from "@/components/EventTracker";

interface Citation {
  title: string;
  url: string;
}

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  citations?: Citation[];
}

export default function Home() {
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [userId, setUserId] = useState("");
  const [sessionId, setSessionId] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [selectedModel, setSelectedModel] = useState("gpt-4o-mini");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Generate or retrieve user ID
    let id = localStorage.getItem("user_id");
    if (!id) {
      id = crypto.randomUUID();
      localStorage.setItem("user_id", id);
    }
    setUserId(id);

    // Generate session ID
    let sId = sessionStorage.getItem("session_id");
    if (!sId) {
      sId = crypto.randomUUID();
      sessionStorage.setItem("session_id", sId);
    }
    setSessionId(sId);
  }, []);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const addMessage = (role: "user" | "assistant", content: string, citations?: Citation[]) => {
    setMessages((prev) => [...prev, { role, content, citations, timestamp: new Date() }]);
  };

  return (
    <main className="h-screen flex flex-col bg-gradient-to-br from-blue-50 to-indigo-100">
      <header className="flex-shrink-0 py-6 px-8 text-center border-b border-gray-200 bg-white/80 backdrop-blur-sm">
        <h1 className="text-3xl font-bold text-gray-800 mb-1">
          LLM Brand Experiment
        </h1>
        <p className="text-gray-600 text-sm">
          Explore brands and products with AI-powered insights
        </p>
      </header>

      <div className="flex-1 overflow-hidden flex flex-col max-w-4xl w-full mx-auto">
        <MessageHistory
          messages={messages}
          userId={userId}
          sessionId={sessionId}
          messagesEndRef={messagesEndRef}
        />

        <div className="flex-shrink-0 bg-white border-t border-gray-200 p-4">
          <QueryBox
            query={query}
            setQuery={setQuery}
            addMessage={addMessage}
            userId={userId}
            sessionId={sessionId}
            isLoading={isLoading}
            setIsLoading={setIsLoading}
            selectedModel={selectedModel}
            setSelectedModel={setSelectedModel}
          />
        </div>
      </div>

      <EventTracker userId={userId} sessionId={sessionId} />
    </main>
  );
}
