"use client";

import { useState, useEffect, useRef } from "react";
import QueryBox from "@/components/QueryBox";
import MessageHistory from "@/components/MessageHistory";
import EventTracker from "@/components/EventTracker";
import Sidebar from "@/components/Sidebar";
import TermsModal from "@/components/TermsModal";
import ClearUserModal from "@/components/ClearUserModal";
import { useSession } from "@/lib/useSession";
import { useEventTracking } from "@/lib/useEventTracking";

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

interface ChatSession {
  id: string;
  title: string;
  messages: Message[];
  lastMessage?: string;
  timestamp: Date;
}

const DEFAULT_EXPERIMENT_ID = "production_v1";
const EXPERIMENT_ID_KEY = "experiment_id_global";

interface LocationData {
  latitude: number;
  longitude: number;
  accuracy?: number;
}

export default function Home() {
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [userId, setUserId] = useState("");
  const [sessionId, setSessionId] = useState("");
  const [experimentId, setExperimentId] = useState("");
  const [showExperimentModal, setShowExperimentModal] = useState(false);
  const [experimentDraft, setExperimentDraft] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [selectedModel, setSelectedModel] = useState("gpt-4o-mini");
  const [location, setLocation] = useState<LocationData | null>(null);
  const [locationReady, setLocationReady] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [showTermsModal, setShowTermsModal] = useState(false);
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [showClearUserModal, setShowClearUserModal] = useState(false);
  const [, setMemoryContext] = useState<Record<string, unknown> | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Check if user has already accepted terms
    const hasAcceptedTerms = localStorage.getItem("terms_accepted");
    if (hasAcceptedTerms === "true") {
      setTermsAccepted(true);
    } else {
      setShowTermsModal(true);
    }

    // Generate or retrieve unique user ID (UUID)
    let id = localStorage.getItem("user_id");
    if (!id) {
      id = crypto.randomUUID();
      localStorage.setItem("user_id", id);
    }
    setUserId(id);

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

  useEffect(() => {
    if (!sessionId) {
      return;
    }

    let cancelled = false;
    setLocationReady(false);

    if (!("geolocation" in navigator)) {
      setLocation(null);
      setLocationReady(true);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        if (cancelled) return;
        setLocation({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy: position.coords.accuracy,
        });
        setLocationReady(true);
      },
      (error) => {
        console.warn("Geolocation error:", error);
        if (cancelled) return;
        setLocation(null);
        setLocationReady(true);
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );

    return () => {
      cancelled = true;
    };
  }, [sessionId]);

  useEffect(() => {
    const stored = localStorage.getItem(EXPERIMENT_ID_KEY);
    if (stored) {
      setExperimentId(stored);
      setExperimentDraft(stored);
      setShowExperimentModal(false);
    } else {
      setExperimentId("");
      setExperimentDraft("");
      setShowExperimentModal(true);
    }
  }, []);

  // NEW: Initialize session-based tracking (using the same sessionId as chat)
  useSession({
    userId: userId || "anonymous",
    sessionId: sessionId,  // Use the same sessionId as chat
    modelGroup: selectedModel,
    experimentId: experimentId,
    location,
    locationReady,
  });

  // NEW: Initialize event tracking (using the same sessionId as chat)
  useEventTracking({
    sessionId: sessionId,  // Use the same sessionId as chat
    trackScroll: true,
    trackClicks: true,
    trackHover: true,
    trackSelection: true,
    trackActivity: true,
    trackZoom: true,
  });

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

  const persistExperiment = (value: string) => {
    localStorage.setItem(EXPERIMENT_ID_KEY, value);
    setExperimentId(value);
    setShowExperimentModal(false);
  };

  const handleExperimentSave = () => {
    if (!experimentDraft.trim() || !sessionId) return;
    const value = experimentDraft.trim();
    persistExperiment(value);
  };

  const handleExperimentSkip = () => {
    if (!sessionId) return;
    persistExperiment(DEFAULT_EXPERIMENT_ID);
  };

  const loadSession = (sId: string) => {
    if (!userId) return;
    try {
      const sessionsData = localStorage.getItem(`chat_sessions_${userId}`);
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
    if (!userId) return;
    try {
      const sessionsData = localStorage.getItem(`chat_sessions_${userId}`);
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

      localStorage.setItem(`chat_sessions_${userId}`, JSON.stringify(sessions));
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
    setMemoryContext(null);
  };

  const handleSelectSession = (sId: string) => {
    // Save current session first
    if (messages.length > 0 && sessionId !== sId) {
      saveCurrentSession();
    }

    // Load selected session
    setSessionId(sId);
    sessionStorage.setItem("session_id", sId);
    setMemoryContext(null);
    loadSession(sId);
  };

  const addMessage = (role: "user" | "assistant", content: string, citations?: Citation[], product_cards?: ProductCardData[], attachments?: { type: string; base64?: string; name?: string }[]) => {
    setMessages((prev) => [...prev, { role, content, citations, product_cards, attachments, timestamp: new Date() }]);
  };

  const handleAcceptTerms = () => {
    localStorage.setItem("terms_accepted", "true");
    setTermsAccepted(true);
    setShowTermsModal(false);
  };

  const handleDeclineTerms = () => {
    // Optionally redirect or show a message
    alert("You must accept the terms to use this service.");
  };

  const handleClearUser = () => {
    // Clear all user data from localStorage
    const oldUserId = localStorage.getItem("user_id");
    if (oldUserId) {
      localStorage.removeItem(`chat_sessions_${oldUserId}`);
    }
    localStorage.removeItem("user_id");
    localStorage.removeItem("terms_accepted");
    sessionStorage.clear();

    // Reload the page to start fresh
    window.location.reload();
  };

  return (
    <div className="h-screen flex">
      {showExperimentModal && (
        <ExperimentModal
          value={experimentDraft}
          onChange={setExperimentDraft}
          onConfirm={handleExperimentSave}
          onSkip={handleExperimentSkip}
        />
      )}

      {/* Terms Modal */}
      <TermsModal
        isOpen={showTermsModal}
        onAccept={handleAcceptTerms}
        onDecline={handleDeclineTerms}
      />

      {/* Clear User Modal */}
      <ClearUserModal
        isOpen={showClearUserModal}
        onConfirm={handleClearUser}
        onCancel={() => setShowClearUserModal(false)}
      />

      {/* Sidebar */}
      <Sidebar
        currentSessionId={sessionId}
        userId={userId}
        onNewChat={handleNewChat}
        onSelectSession={handleSelectSession}
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
        onShowTerms={() => setShowTermsModal(true)}
        onShowClearUserModal={() => setShowClearUserModal(true)}
      />

      {/* Main content area */}
      <main
        className={`flex-1 flex flex-col bg-gradient-to-br from-blue-50 to-indigo-100 transition-all duration-300 overflow-hidden ${
          sidebarOpen ? "lg:ml-64" : ""
        }`}
      >
        {messages.length === 0 ? (
          /* Centered layout for new chat */
          <div className="flex-1 flex flex-col items-center justify-center p-8">
            <div className="max-w-3xl w-full space-y-8">
              {/* Centered Title */}
              <div className="text-center space-y-3">
                <h1 className="text-4xl font-bold text-gray-800">
                  LLM Brand Experiment
                </h1>
                <p className="text-gray-600 text-lg">
                  Explore brands and products with AI-powered insights
                </p>
              </div>

              {/* Centered Query Box */}
              <div className="bg-white rounded-xl shadow-lg p-6">
                <QueryBox
                  query={query}
                  setQuery={setQuery}
                  addMessage={addMessage}
                  setMemoryContext={setMemoryContext}
                  userId={userId}
                  sessionId={sessionId}
                  isLoading={isLoading}
                  setIsLoading={setIsLoading}
                  selectedModel={selectedModel}
                  setSelectedModel={setSelectedModel}
                  messages={messages}
                  location={location}
                />
              </div>
            </div>
          </div>
        ) : (
          /* Normal layout with header and messages */
          <>
            <header className="flex-shrink-0 py-6 px-8 text-center border-b border-gray-200 bg-white/80 backdrop-blur-sm">
              <h1 className="text-3xl font-bold text-gray-800 mb-1">
                LLM Brand Experiment
              </h1>
              <p className="text-gray-600 text-sm">
                Explore brands and products with AI-powered insights
              </p>
            </header>

            {/* Message area */}
            <div className="flex-1 overflow-y-auto">
              <div className="max-w-4xl w-full mx-auto">
                <MessageHistory
                  messages={messages}
                  userId={userId}
                  sessionId={sessionId}
                  messagesEndRef={messagesEndRef}
                  isLoading={isLoading}
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
                  setMemoryContext={setMemoryContext}
                  userId={userId}
                  sessionId={sessionId}
                  isLoading={isLoading}
                  setIsLoading={setIsLoading}
                  selectedModel={selectedModel}
                  setSelectedModel={setSelectedModel}
                  messages={messages}
                  location={location}
                />
              </div>
            </div>
          </>
        )}

        <EventTracker userId={userId} sessionId={sessionId} />
      </main>
    </div>
  );
}

function ExperimentModal({
  value,
  onChange,
  onConfirm,
  onSkip,
}: {
  value: string;
  onChange: (val: string) => void;
  onConfirm: () => void;
  onSkip: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <div className="bg-white rounded-lg shadow-2xl w-full max-w-md p-6 space-y-4">
        <div>
          <h2 className="text-xl font-semibold text-gray-800">Set Experiment ID</h2>
          <p className="text-sm text-gray-600 mt-1">
            Enter the experiment identifier for this session. This value will be saved with your session logs.
          </p>
        </div>
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="e.g. marketing_test_a"
          autoFocus
          onKeyDown={(e) => {
            if (e.key === "Enter" && value.trim()) {
              e.preventDefault();
              onConfirm();
            }
          }}
        />
        <div className="flex gap-3">
          <button
            type="button"
            className="w-1/2 py-2 rounded-md font-semibold text-gray-700 border border-gray-300 hover:bg-gray-100 transition-colors"
            onClick={onSkip}
          >
            Skip (use default)
          </button>
          <button
            type="button"
            disabled={!value.trim()}
            onClick={onConfirm}
            className={`w-1/2 py-2 rounded-md font-semibold text-white transition-colors ${
              value.trim() ? "bg-blue-600 hover:bg-blue-700" : "bg-gray-400 cursor-not-allowed"
            }`}
          >
            Save ID
          </button>
        </div>
      </div>
    </div>
  );
}
