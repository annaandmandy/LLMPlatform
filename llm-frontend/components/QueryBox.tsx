"use client";

import { useState } from "react";
import Clarity from "@microsoft/clarity";

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
  citations?: Citation[];
  product_cards?: ProductCardData[];
  attachments?: AttachedMedia[];
}

interface QueryBoxProps {
  query: string;
  setQuery: (query: string) => void;
  addMessage: (
    role: "user" | "assistant",
    content: string,
    citations?: Citation[],
    product_cards?: ProductCardData[],
    attachments?: { type: string; base64?: string; name?: string }[]
  ) => void;
  setMemoryContext?: (context: any) => void;
  userId: string;
  sessionId: string;
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
  selectedModel: string;
  setSelectedModel: (model: string) => void;
  location?: {
    latitude: number;
    longitude: number;
    accuracy?: number;
  } | null;
  messages?: Message[];
}

interface AttachedMedia {
  name: string;
  type: "image";
  previewUrl: string;
  dataUrl: string;
  mime: string;
  size: number;
}

const MAX_IMAGE_DIMENSION = 1200; // px
const MAX_IMAGE_BYTES = 1.5 * 1024 * 1024; // ~1.5MB

const dataUrlByteLength = (dataUrl: string) => {
  const base64 = dataUrl.split(",")[1] || "";
  return Math.ceil((base64.length * 3) / 4);
};

async function resizeImageIfNeeded(
  dataUrl: string,
  mime: string,
  maxDim = MAX_IMAGE_DIMENSION,
  maxBytes = MAX_IMAGE_BYTES,
): Promise<{ dataUrl: string; mime: string; size: number }> {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => {
      const { width, height } = img;
      const needsResize = width > maxDim || height > maxDim || dataUrlByteLength(dataUrl) > maxBytes;
      if (!needsResize) {
        resolve({ dataUrl, mime, size: dataUrlByteLength(dataUrl) });
        return;
      }

      const scale = Math.min(maxDim / width, maxDim / height, 1);
      const targetW = Math.round(width * scale);
      const targetH = Math.round(height * scale);
      const canvas = document.createElement("canvas");
      canvas.width = targetW;
      canvas.height = targetH;
      const ctx = canvas.getContext("2d");
      if (!ctx) {
        resolve({ dataUrl, mime, size: dataUrlByteLength(dataUrl) });
        return;
      }
      ctx.drawImage(img, 0, 0, targetW, targetH);
      const outMime = mime === "image/png" ? "image/png" : "image/jpeg";
      const outDataUrl = canvas.toDataURL(outMime, 0.82);
      resolve({ dataUrl: outDataUrl, mime: outMime, size: dataUrlByteLength(outDataUrl) });
    };
    img.onerror = () => resolve({ dataUrl, mime, size: dataUrlByteLength(dataUrl) });
    img.src = dataUrl;
  });
}

// ✅ Expanded models with provider info (and web-search enabled)
const AVAILABLE_MODELS = [
  { id: "gpt-4o-mini-search-preview", name: "GPT-4o mini", provider: "openai" },
  { id: "gpt-4o-search-preview", name: "GPT-4o", provider: "openai" },
  { id: "gpt-5-search-api", name: "GPT-5", provider: "openai" },
  { id: "x-ai/grok-3-mini:online", name: "Grok 3 mini", provider: "openrouter" },
  { id: "perplexity/sonar:online", name: "Perplexity Sonar", provider: "openrouter" },
  { id: "claude-sonnet-4-5-20250929", name: "Claude 4.5 Sonnet", provider: "anthropic" },
  { id: "gemini-2.5-flash", name: "Gemini 2.5 Flash", provider: "google" },

];

export default function QueryBox({
  query,
  setQuery,
  addMessage,
  setMemoryContext,
  userId,
  sessionId,
  isLoading,
  setIsLoading,
  selectedModel,
  setSelectedModel,
  location,
  messages = [],
}: QueryBoxProps) {
  const [error, setError] = useState("");
  const [showModelSelector, setShowModelSelector] = useState(false);
  const [attachments, setAttachments] = useState<AttachedMedia[]>([]);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    const accepted = files.filter((f) => f.type.startsWith("image/"));
    const converts = await Promise.all(
      accepted.map(
        (file) =>
          new Promise<AttachedMedia>((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = async () => {
              try {
                const originalUrl = reader.result as string;
                const resized = await resizeImageIfNeeded(originalUrl, file.type);
                resolve({
                  name: file.name,
                  type: "image",
                  previewUrl: resized.dataUrl,
                  dataUrl: resized.dataUrl,
                  mime: resized.mime,
                  size: resized.size,
                });
              } catch (err) {
                reject(err || new Error("Failed to process image"));
              }
            };
            reader.onerror = () => reject(reader.error || new Error("Failed to read file"));
            reader.readAsDataURL(file);
          }),
      ),
    );
    setAttachments((prev) => [...prev, ...converts]);
    e.target.value = "";
  };

  const removeAttachment = (name: string) => {
    setAttachments((prev) => prev.filter((a) => a.name !== name));
  };

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

    const historyPayload =
      messages.length > 0 ? messages.slice(-6).map(({ role, content }) => ({ role, content })) : [];
    const attachmentPayload = attachments.map((a) => ({
      type: a.type,
      name: a.name,
      mime: a.mime,
      base64: a.dataUrl,
      size: a.size,
    }));

    setIsLoading(true);
    setError("");

    const userQuery = query;
    addMessage("user", userQuery, undefined, undefined, attachments.map((a) => ({ type: a.type, base64: a.dataUrl, name: a.name })));
    setQuery("");

    // set up clarity tag
    const currentModel = AVAILABLE_MODELS.find((m) => m.id === selectedModel) || AVAILABLE_MODELS[0];
    const modelProvider = currentModel?.provider || "openai";
    try {
      Clarity.setTag("selected_model", currentModel.id);
      Clarity.setTag("selected_model_name", currentModel.name);
      Clarity.setTag("selected_model_provider", modelProvider);
    } catch (err) {
      console.warn("Clarity tagging failed:", err);
    }

    try {
      const backendUrl = (process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000").replace(/\/$/, "");

      const res = await fetch(`${backendUrl}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          session_id: sessionId,
          query: userQuery,
          model_name: currentModel.id,
          model_provider: modelProvider,
          web_search: true, // still pass through for legacy behavior
          // Always include memory context bundle; intent classifier handles product search server-side
          use_memory: true,
          history: historyPayload,
          location,
          attachments: attachmentPayload,
        }),
      });

      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);

      const data = await res.json();
      addMessage("assistant", data.response, data.citations, data.product_cards, data.attachments);
      if (setMemoryContext) {
        setMemoryContext(data.memory_context || null);
      }
      // Clear attachments after send
      setAttachments([]);

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

  const currentModel = AVAILABLE_MODELS.find((m) => m.id === selectedModel) || AVAILABLE_MODELS[0];

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
            <div className="absolute right-0 bottom-full mb-2 w-64 bg-white rounded-lg shadow-xl border border-gray-200 z-10 max-h-80 overflow-y-auto">
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

        {/* Attachments */}
        {attachments.length > 0 && (
          <div className="flex flex-wrap gap-3">
            {attachments.map((a) => (
              <div key={a.name} className="relative w-20 h-20 rounded-lg overflow-hidden border border-gray-200">
                <img src={a.previewUrl} alt={a.name} className="w-full h-full object-cover" />
                <button
                  type="button"
                  onClick={() => removeAttachment(a.name)}
                  className="absolute -top-2 -right-2 bg-white text-gray-700 rounded-full shadow p-1"
                  aria-label="Remove attachment"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Input Area */}
        <div className="flex gap-2">
          <label className="flex items-center justify-center w-12 h-12 bg-white border border-gray-300 rounded-lg hover:bg-gray-100 cursor-pointer transition-colors">
            <input
              type="file"
              accept="image/*"
              className="hidden"
              onChange={handleFileChange}
            />
            <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
          </label>
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
