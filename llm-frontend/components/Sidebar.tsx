"use client";

import { useState, useEffect } from "react";

interface ChatSession {
  id: string;
  title: string;
  lastMessage?: string;
  timestamp: Date;
}

interface SidebarProps {
  currentSessionId: string;
  userId: string;
  onNewChat: () => void;
  onSelectSession: (sessionId: string) => void;
  isOpen: boolean;
  onToggle: () => void;
  onShowTerms: () => void;
  onShowClearUserModal: () => void;
}

export default function Sidebar({
  currentSessionId,
  userId,
  onNewChat,
  onSelectSession,
  isOpen,
  onToggle,
  onShowTerms,
  onShowClearUserModal,
}: SidebarProps) {

  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [isLoadingSessions, setIsLoadingSessions] = useState(false);
  const [showClearConfirm, setShowClearConfirm] = useState(false);

  // Load chat sessions from localStorage
  const loadSessions = () => {
    if (!userId) return;
    try {
      setIsLoadingSessions(true);
      const savedSessions = localStorage.getItem(`chat_sessions_${userId}`);
      if (savedSessions) {
        const parsed = JSON.parse(savedSessions);
        // Convert timestamp strings back to Date objects
        const sessionsWithDates = parsed.map((s: any) => ({
          ...s,
          timestamp: new Date(s.timestamp),
        }));
        setSessions(sessionsWithDates);
      } else {
        setSessions([]);
      }
    } catch (error) {
      console.error("Error loading sessions:", error);
    } finally {
      setIsLoadingSessions(false);
    }
  };

  // Clear all chat history
  const handleClearHistory = () => {
    if (!userId) return;
    try {
      localStorage.removeItem(`chat_sessions_${userId}`);
      setSessions([]);
      setShowClearConfirm(false);
      onNewChat(); // Start a fresh chat
    } catch (error) {
      console.error("Error clearing sessions:", error);
    }
  };

  // Delete a single session
  const handleDeleteSession = (sessionId: string, event: React.MouseEvent) => {
    if (!userId) return;
    event.stopPropagation(); // Prevent selecting the session
    try {
      const updatedSessions = sessions.filter((s) => s.id !== sessionId);
      setSessions(updatedSessions);
      localStorage.setItem(`chat_sessions_${userId}`, JSON.stringify(updatedSessions));

      // If deleting current session, start a new chat
      if (sessionId === currentSessionId) {
        onNewChat();
      }
    } catch (error) {
      console.error("Error deleting session:", error);
    }
  };

  // Load sessions when sidebar opens
  useEffect(() => {
    if (isOpen) {
      loadSessions();
    }
  }, [isOpen]);

  const formatTimestamp = (date: Date) => {
    const now = new Date();
    const diffInMs = now.getTime() - date.getTime();
    const diffInHours = diffInMs / (1000 * 60 * 60);
    const diffInDays = diffInMs / (1000 * 60 * 60 * 24);

    if (diffInHours < 24) {
      return "Today";
    } else if (diffInDays < 7) {
      return `${Math.floor(diffInDays)} days ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onToggle}
        />
      )}

      {/* Sidebar */}
      <div
        className={`fixed top-0 left-0 h-full bg-gray-700 text-gray-50 w-64 transform transition-transform duration-300 z-50 flex flex-col shadow-xl ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* Header */}
        <div className="p-4 border-b border-gray-500 flex justify-between items-center">
          <h2 className="text-lg font-semibold">Chat History</h2>
          <button
            onClick={onToggle}
            className="p-1.5 hover:bg-gray-600 rounded-lg transition-colors"
            aria-label="Close sidebar"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* New Chat Button */}
        <div className="p-3 border-b border-gray-500">
          <button
            onClick={() => {
              onNewChat();
              loadSessions(); // Refresh sessions list
            }}
            className="w-full flex items-center gap-2 px-4 py-3 bg-blue-500 hover:bg-blue-600 rounded-lg transition-colors font-medium"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            New Chat
          </button>
        </div>

        {/* Chat Sessions List */}
        <div className="flex-1 overflow-y-auto p-3">
          {isLoadingSessions ? (
            <div className="text-center text-gray-300 py-4">
              <div className="animate-spin w-6 h-6 border-2 border-gray-300 border-t-transparent rounded-full mx-auto"></div>
            </div>
          ) : sessions.length === 0 ? (
            <div className="text-center text-gray-400 py-8 text-sm">
              No chat history yet.
              <br />
              Start a new conversation!
            </div>
          ) : (
            <div className="space-y-2">
              {sessions.map((session) => (
                <div
                  key={session.id}
                  className={`group relative rounded-lg transition-colors ${
                    currentSessionId === session.id
                      ? "bg-gray-600"
                      : "hover:bg-gray-600"
                  }`}
                >
                  <button
                    onClick={() => {
                      onSelectSession(session.id);
                      if (window.innerWidth < 1024) {
                        onToggle(); // Close sidebar on mobile after selection
                      }
                    }}
                    className="w-full text-left px-3 py-3 pr-10"
                  >
                    <div className="flex items-start gap-2">
                      <svg className="w-4 h-4 mt-0.5 flex-shrink-0 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                      </svg>
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-sm truncate">
                          {session.title}
                        </div>
                        {session.lastMessage && (
                          <div className="text-xs text-gray-400 truncate mt-0.5">
                            {session.lastMessage}
                          </div>
                        )}
                        <div className="text-xs text-gray-500 mt-1">
                          {formatTimestamp(session.timestamp)}
                        </div>
                      </div>
                    </div>
                  </button>
                  {/* Delete button */}
                  <button
                    onClick={(e) => handleDeleteSession(session.id, e)}
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 hover:bg-red-600 rounded opacity-0 group-hover:opacity-100 transition-opacity"
                    aria-label="Delete chat"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Clear History Section */}
        {sessions.length > 0 && (
          <div className="p-3 border-t border-gray-500">
            {showClearConfirm ? (
              <div className="space-y-2">
                <p className="text-xs text-gray-200 text-center">Clear all chat history?</p>
                <div className="flex gap-2">
                  <button
                    onClick={handleClearHistory}
                    className="flex-1 px-3 py-2 bg-red-500 hover:bg-red-600 text-white text-sm rounded-lg transition-colors"
                  >
                    Yes, Clear All
                  </button>
                  <button
                    onClick={() => setShowClearConfirm(false)}
                    className="flex-1 px-3 py-2 bg-gray-600 hover:bg-gray-500 text-white text-sm rounded-lg transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <button
                onClick={() => setShowClearConfirm(true)}
                className="w-full flex items-center justify-center gap-2 px-3 py-2 text-sm text-gray-200 hover:text-white hover:bg-gray-600 rounded-lg transition-colors"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                Clear All History
              </button>
            )}
          </div>
        )}

        {/* Footer - User Info & Actions */}
        <div className="p-4 border-t border-gray-500 space-y-3">
          {/* User Info */}
          <div className="flex items-center gap-3">
            {/* User Avatar */}
            <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center flex-shrink-0">
              <span className="text-sm font-semibold">U</span>
            </div>

            {/* User Info */}
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium">Anonymous User</div>
              <div className="text-xs text-gray-300">ID: {userId.slice(0, 8)}...</div>
            </div>

            {/* Clear User Button */}
            <button
              onClick={onShowClearUserModal}
              className="p-1.5 hover:bg-red-600 rounded-lg transition-colors flex-shrink-0 group"
              aria-label="Clear user and start fresh"
              title="Clear user and start fresh"
            >
              <svg className="w-4 h-4 text-gray-300 group-hover:text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
          </div>

          {/* Terms & Privacy Link */}
          <button
            onClick={onShowTerms}
            className="w-full text-left px-2 py-1.5 text-xs text-gray-300 hover:text-white hover:bg-gray-600 rounded transition-colors"
          >
            Terms of Use & Privacy Policy
          </button>
        </div>
      </div>

      {/* Toggle button (visible when sidebar is closed) */}
      {!isOpen && (
        <button
          onClick={onToggle}
          className="fixed top-4 left-4 z-30 p-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-colors shadow-lg"
          aria-label="Open sidebar"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
      )}
    </>
  );
}
