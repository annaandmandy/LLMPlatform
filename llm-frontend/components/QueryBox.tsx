"use client";

import { useState } from "react";

interface Citation {
  title: string;
  url: string;
}

interface QueryBoxProps {
  query: string;
  setQuery: (query: string) => void;
  addMessage: (role: "user" | "assistant", content: string, citations?: Citation[]) => void;
  userId: string;
  sessionId: string;
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
  selectedModel: string;
  setSelectedModel: (model: string) => void;
}

// ✅ Expanded models with provider info (and web-search enabled)
const AVAILABLE_MODELS = [
  { id: "gpt-5", name: "GPT-5", provider: "openai" },
  { id: "openrouter/xai/grok-3", name: "Grok 3 🌐", provider: "openrouter" },
  { id: "openrouter/perplexity/sonar-small-online", name: "Perplexity Sonar Small 🌐", provider: "openrouter" },
  { id: "anthropic/claude-3-5-sonnet", name: "Claude 3.5 Sonnet", provider: "anthropic" },
];

export default function QueryBox({
  query,
  setQuery,
  addMessage,
  userId,
  sessionId,
  isLoading,
  setIsLoading,
  selectedModel,
  setSelectedModel,
}: QueryBoxProps) {
  const [error, setError] = useState("");
  const [showModelSelector, setShowModelSelector] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!query.trim()) {
      setError("Please enter a query");
      return;
    }

    if (!userId || !sessionId) {
      setError("User session not initialized");
      return;
    }

    setIsLoading(true);
    setError("");

    const userQuery = query;
    addMessage("user", userQuery);
    setQuery("");

    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

      // ✅ find provider based on selected model
      const currentModel = AVAILABLE_MODELS.find((m) => m.id === selectedModel) || { id: "openai/gpt-4o-mini", name: "GPT-4o Mini", provider: "openai" };
      const modelProvider = currentModel?.provider || "openrouter";

      const res = await fetch(`${backendUrl}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          session_id: sessionId,
          query: userQuery,
          model_name: currentModel.id,
          model_provider: modelProvider,
          web_search: true, // ✅ always enable web search
        }),
      });

      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);

      const data = await res.json();
      addMessage("assistant", data.response, data.citations);

      // ✅ log browsing event
      await fetch(`${backendUrl}/log_event`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          session_id: sessionId,
          event_type: "browse",
          query: userQuery,
          page_url: window.location.href,
        }),
      });
    } catch (err) {
      setError(`Failed to fetch response: ${err instanceof Error ? err.message : "Unknown error"}`);
      console.error("Error fetching query:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const currentModel = AVAILABLE_MODELS.find((m) => m.id === selectedModel);

  return (
    <div className="w-full">
      <form onSubmit={handleSubmit} className="space-y-3">
        {/* Model Selector */}
        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-600">
            Model:{" "}
            <span className="font-semibold text-gray-800">
              {currentModel?.name}
            </span>
          </div>
          <div className="relative">
            <button
              type="button"
              onClick={() => setShowModelSelector(!showModelSelector)}
              className="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-md transition-colors flex items-center gap-2"
            >
              Change Model
              <svg
                className={`w-4 h-4 transition-transform ${showModelSelector ? "rotate-180" : ""}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            {showModelSelector && (
              <div className="absolute right-0 mt-2 w-64 bg-white rounded-lg shadow-xl border border-gray-200 z-10">
                <div className="p-2">
                  {AVAILABLE_MODELS.map((model) => (
                    <button
                      key={model.id}
                      type="button"
                      onClick={() => {
                        setSelectedModel(model.id);
                        setShowModelSelector(false);
                      }}
                      className={`w-full text-left px-3 py-2 rounded-md transition-colors ${
                        selectedModel === model.id
                          ? "bg-blue-100 text-blue-800"
                          : "hover:bg-gray-100 text-gray-700"
                      }`}
                    >
                      <div className="font-medium">{model.name}</div>
                      <div className="text-xs text-gray-500">{model.provider}</div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Input Area */}
        <div className="flex gap-2">
          <textarea
            id="query"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type your message..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none text-gray-800"
            rows={2}
            disabled={isLoading}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e);
              }
            }}
          />
          <button
            type="submit"
            disabled={isLoading || !query.trim()}
            className="px-6 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold rounded-lg transition-colors duration-200 flex items-center justify-center"
          >
            {isLoading ? (
              <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            ) : (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            )}
          </button>
        </div>

        {error && <div className="text-red-600 text-sm bg-red-50 p-2 rounded-lg">{error}</div>}
      </form>
    </div>
  );
}
