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
    <form onSubmit={handleSubmit} className="w-full">
      <div className="flex items-center gap-3 bg-white rounded-2xl shadow-sm border border-gray-200 px-4 py-3">

        {/* Left Icons */}
        <div className="flex items-center gap-3 text-gray-500">
          {/* Model Selector Icon */}
          <button
            type="button"
            onClick={() => setShowModelSelector(!showModelSelector)}
            className="hover:text-gray-700 transition"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M4 7h12M4 12h16M4 17h10" />
            </svg>
          </button>

          {/* Attachment */}
          <label className="cursor-pointer hover:text-gray-700 transition">
            <input type="file" accept="image/*" className="hidden" onChange={handleFileChange}/>
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
                d="M4 5h16v14H4z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
                d="M4 15l4-4 3 3 5-5 4 4" />
              <circle cx="9" cy="9" r="1.5" />
            </svg>
          </label>
        </div>

        {/* Input */}
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={`Message ${currentModel?.name}`}
          rows={1}
          className="flex-1 resize-none bg-transparent focus:outline-none text-gray-800 placeholder-gray-400"
          disabled={isLoading}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSubmit(e);
            }
          }}
        />

        {/* Right Icons */}
        <div className="flex items-center gap-3">

          {/* Send */}
          <button
            type="submit"
            disabled={isLoading || !query.trim()}
            className="w-10 h-10 rounded-full bg-gray-100 hover:bg-gray-200 flex items-center justify-center transition disabled:opacity-40 disabled:hover:bg-gray-100"
          >
            {isLoading ? (
              <svg className="animate-spin w-5 h-5 text-gray-500" viewBox="0 0 24 24">
                <circle className="opacity-20" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                <path className="opacity-80" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
              </svg>
            ) : (
              <svg className="w-5 h-5 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" d="M12 19l9 2-9-18-9 18 9-2z"/>
              </svg>
            )}
          </button>
        </div>
      </div>

      {/* Model Selector Dropdown */}
      {showModelSelector && (
        <div className="mt-2 bg-white rounded-xl shadow-lg border border-gray-200 p-2 w-64">
          {AVAILABLE_MODELS.map((model) => (
            <button
              key={model.id}
              type="button"
              onClick={() => {
                setSelectedModel(model.id);
                setShowModelSelector(false);
              }}
              className={`w-full text-left px-3 py-2 rounded-lg transition ${
                selectedModel === model.id ? 'bg-blue-100 text-blue-800' : 'hover:bg-gray-100'
              }`}
            >
              <div className="font-medium">{model.name}</div>
              <div className="text-xs text-gray-500">{model.provider}</div>
            </button>
          ))}
        </div>
      )}

      {error && <div className="text-red-600 text-sm mt-2">{error}</div>}
    </form>
  );


}
