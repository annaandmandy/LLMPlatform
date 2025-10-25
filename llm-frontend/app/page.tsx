"use client";

import { useState, useEffect, useRef } from "react";
import QueryBox from "@/components/QueryBox";
import MessageHistory from "@/components/MessageHistory";
import EventTracker from "@/components/EventTracker";
import Sidebar from "@/components/Sidebar";

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

interface ChatSession {
  id: string;
  title: string;
  messages: Message[];
  lastMessage?: string;
  timestamp: Date;
}

const DEMO_USER_ID = "demo-user";

export default function Home() {
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [userId, setUserId] = useState("");
  const [sessionId, setSessionId] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [selectedModel, setSelectedModel] = useState("gpt-4o-mini");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Use demo user ID for now
    setUserId(DEMO_USER_ID);
    localStorage.setItem("user_id", DEMO_USER_ID);

    // Generate or load session ID
    let sId = sessionStorage.getItem("session_id");
    if (!sId) {
      sId = crypto.randomUUID();
      sessionStorage.setItem("session_id", sId);
    }
    setSessionId(sId);

    // Try to load existing session
    loadSession(sId);
  }, []);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Save session whenever messages change
  useEffect(() => {
    if (messages.length > 0 && sessionId) {
      saveCurrentSession();
    }
  }, [messages, sessionId]);

  const loadSession = (sId: string) => {
    try {
      const sessionsData = localStorage.getItem(`chat_sessions_${DEMO_USER_ID}`);
      if (sessionsData) {
        const sessions: ChatSession[] = JSON.parse(sessionsData);
        const session = sessions.find((s) => s.id === sId);
        if (session) {
          // Restore messages with Date objects
          const restoredMessages = session.messages.map((m) => ({
            ...m,
            timestamp: new Date(m.timestamp),
          }));
          setMessages(restoredMessages);
        }
      }
    } catch (error) {
      console.error("Error loading session:", error);
    }
  };

  const saveCurrentSession = () => {
    try {
      const sessionsData = localStorage.getItem(`chat_sessions_${DEMO_USER_ID}`);
      let sessions: ChatSession[] = sessionsData ? JSON.parse(sessionsData) : [];

      // Generate title from first user message
      const firstUserMessage = messages.find((m) => m.role === "user");
      const title = firstUserMessage
        ? firstUserMessage.content.slice(0, 50) + (firstUserMessage.content.length > 50 ? "..." : "")
        : "New Chat";

      // Get last message for preview
      const lastMsg = messages[messages.length - 1];
      const lastMessage = lastMsg
        ? lastMsg.content.slice(0, 60) + (lastMsg.content.length > 60 ? "..." : "")
        : undefined;

      // Update or add current session
      const existingIndex = sessions.findIndex((s) => s.id === sessionId);
      const sessionData: ChatSession = {
        id: sessionId,
        title,
        messages,
        lastMessage,
        timestamp: new Date(),
      };

      if (existingIndex >= 0) {
        sessions[existingIndex] = sessionData;
      } else {
        sessions.unshift(sessionData); // Add to beginning
      }

      // Keep only last 50 sessions
      sessions = sessions.slice(0, 50);

      localStorage.setItem(`chat_sessions_${DEMO_USER_ID}`, JSON.stringify(sessions));
    } catch (error) {
      console.error("Error saving session:", error);
    }
  };

  const handleNewChat = () => {
    // Save current session before creating new one
    if (messages.length > 0) {
      saveCurrentSession();
    }

    // Create new session
    const newSessionId = crypto.randomUUID();
    setSessionId(newSessionId);
    sessionStorage.setItem("session_id", newSessionId);
    setMessages([]);
    setQuery("");
  };

  const handleSelectSession = (sId: string) => {
    // Save current session first
    if (messages.length > 0 && sessionId !== sId) {
      saveCurrentSession();
    }

    // Load selected session
    setSessionId(sId);
    sessionStorage.setItem("session_id", sId);
    loadSession(sId);
  };

  const addMessage = (role: "user" | "assistant", content: string, citations?: Citation[]) => {
    setMessages((prev) => [...prev, { role, content, citations, timestamp: new Date() }]);
  };

  return (
    <div className="h-screen flex">
      {/* Sidebar */}
      <Sidebar
        currentSessionId={sessionId}
        onNewChat={handleNewChat}
        onSelectSession={handleSelectSession}
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
      />

      {/* Main content area */}
      <main className={`flex-1 flex flex-col bg-gradient-to-br from-blue-50 to-indigo-100 transition-all duration-300 overflow-hidden ${
        sidebarOpen ? "lg:ml-64" : ""
      }`}>
        <header className="flex-shrink-0 py-6 px-8 text-center border-b border-gray-200 bg-white/80 backdrop-blur-sm">
          <h1 className="text-3xl font-bold text-gray-800 mb-1">
            LLM Brand Experiment
          </h1>
          <p className="text-gray-600 text-sm">
            Explore brands and products with AI-powered insights
          </p>
        </header>

        {/* Message area with full-width scrollbar */}
        <div className="flex-1 overflow-y-auto">
          <div className="max-w-4xl w-full mx-auto">
            <MessageHistory
              messages={messages}
              userId={userId}
              sessionId={sessionId}
              messagesEndRef={messagesEndRef}
            />
          </div>
        </div>

        {/* Query box - fixed at bottom */}
        <div className="flex-shrink-0 bg-white border-t border-gray-200">
          <div className="max-w-4xl w-full mx-auto p-4">
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
    </div>
  );
}
