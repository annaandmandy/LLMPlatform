"use client";

import { useEffect, useRef, useState } from "react";
import Clarity from "@microsoft/clarity";

interface QueryBoxProps {
  query: string;
  setQuery: (query: string) => void;
  onSendMessage: (query: string, attachments: AttachedMedia[]) => Promise<void>;
  userId: string;
  sessionId: string;
  isLoading: boolean;
  selectedModel: string;
  setSelectedModel: (model: string) => void;
  isShoppingMode?: boolean;
  onToggleShoppingMode?: () => void;
  isReadOnly?: boolean;
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
  onSendMessage,
  userId,
  sessionId,
  isLoading,
  selectedModel,
  setSelectedModel,
  isShoppingMode,
  onToggleShoppingMode,
  isReadOnly = false,
}: QueryBoxProps) {
  const [error, setError] = useState("");
  const [showModelSelector, setShowModelSelector] = useState(false);
  const [attachments, setAttachments] = useState<AttachedMedia[]>([]);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const modelSelectorRef = useRef<HTMLDivElement>(null);

  const logUIInteraction = async (action: string) => {
    if (!sessionId) return;
    try {
      const backendUrl = (process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000").replace(/\/$/, "");
      await fetch(`${backendUrl}/session/event`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          event: {
            t: Date.now(),
            type: "click",
            data: { text: action, label: action },
          },
        }),
      });
    } catch (err) {
      console.warn("Failed to log UI interaction", err);
    }
  };

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (!showModelSelector) return;
      if (!modelSelectorRef.current) return;
      if (modelSelectorRef.current.contains(e.target as Node)) return;
      setShowModelSelector(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [showModelSelector]);

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

    setError("");
    logUIInteraction("send message");

    try {
      await onSendMessage(query, attachments);
      setQuery("");
      setAttachments([]);
    } catch (err) {
      setError("Failed to send message: " + (err instanceof Error ? err.message : String(err)));
    } finally {
      // Keep focus
      textareaRef.current?.focus();
    }
  };

  const currentModel = AVAILABLE_MODELS.find((m) => m.id === selectedModel) || AVAILABLE_MODELS[0];

  return (
    <form onSubmit={handleSubmit} className="w-full relative">
      {/* Image Attachments Preview */}
      {attachments.length > 0 && (
        <div className="flex gap-3 mb-3 flex-wrap">
          {attachments.map((a) => (
            <div
              key={a.name}
              className="relative w-16 h-16 bg-gray-100 rounded-lg overflow-hidden border border-gray-300 shadow-sm"
            >
              <img
                src={a.previewUrl}
                alt={a.name}
                className="w-full h-full object-cover"
              />

              {/* Remove Button */}
              <button
                type="button"
                onClick={() => removeAttachment(a.name)}
                className="absolute -top-1.5 -right-1.5 bg-white shadow-md text-gray-600 hover:text-red-500 rounded-full p-1"
              >
                <svg
                  className="w-3 h-3"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Model selector container - wraps both button trigger and dropdown for click-outside detection */}
      <div ref={modelSelectorRef} className="relative">
        {/* Model Selector Dropdown - positioned above the input */}
        {showModelSelector && (
          <div className="absolute bottom-full left-0 mb-2 bg-white rounded-xl shadow-lg border border-gray-200 p-2 w-64 z-50">
            {AVAILABLE_MODELS.map((model) => (
              <button
                key={model.id}
                type="button"
                onClick={() => {
                  setSelectedModel(model.id);
                  setShowModelSelector(false);
                }}
                className={`w-full text-left px-3 py-2 rounded-lg transition ${selectedModel === model.id ? 'bg-blue-100 text-blue-800' : 'hover:bg-gray-100'
                  }`}
              >
                <div className="font-medium">{model.name}</div>
                <div className="text-xs text-gray-500">{model.provider}</div>
              </button>
            ))}
          </div>
        )}

        <div className="flex items-center gap-3 bg-white rounded-2xl shadow-sm border border-gray-200 px-4 py-3">

          {/* Left Icons */}
          <div className="flex items-center gap-3 text-gray-500">
            {/* Model Selector Icon */}
            <button
              type="button"
              disabled={isReadOnly}
              onClick={() => {
                setShowModelSelector(!showModelSelector);
                logUIInteraction("model switch");
              }}
              className="hover:text-gray-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M4 7h12M4 12h16M4 17h10" />
              </svg>
            </button>

            {/* Attachment */}
            <label
              className={`cursor-pointer hover:text-gray-700 transition ${isReadOnly ? 'opacity-50 cursor-not-allowed' : ''}`}
              onClick={(e) => {
                if (isReadOnly) e.preventDefault();
                else logUIInteraction("image upload");
              }}
            >
              <input type="file" accept="image/*" className="hidden" onChange={handleFileChange} disabled={isReadOnly} />
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
            ref={textareaRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={isReadOnly ? "Read-only view of shared session" : `Message ${currentModel?.name}`}
            rows={1}
            className="flex-1 resize-none bg-transparent focus:outline-none text-gray-800 placeholder-gray-400 disabled:text-gray-400 disabled:cursor-not-allowed"
            disabled={isLoading || isReadOnly}
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
              disabled={isLoading || isReadOnly || (!query.trim() && attachments.length === 0)}
              className="w-10 h-10 rounded-full bg-gray-100 hover:bg-gray-200 flex items-center justify-center transition disabled:opacity-40 disabled:hover:bg-gray-100"
            >
              {isLoading ? (
                <svg className="animate-spin w-5 h-5 text-gray-500" viewBox="0 0 24 24">
                  <circle className="opacity-20" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-80" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
              ) : (
                <svg className="w-5 h-5 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" d="M12 19l9 2-9-18-9 18 9-2z" />
                </svg>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Shopping Mode Toggle - Absolute positioned above input, right side */}
      <div className="absolute bottom-full right-0 mb-3 flex items-center gap-2">
        <span className={`text-sm font-medium ${isShoppingMode ? "text-blue-600" : "text-gray-500"}`}>
          Shopping Mode
        </span>
        <button
          type="button"
          onClick={onToggleShoppingMode}
          className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${isShoppingMode ? "bg-blue-600" : "bg-gray-200"
            }`}
        >
          <span
            className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${isShoppingMode ? "translate-x-6" : "translate-x-1"
              }`}
          />
        </button>
      </div>

      {error && <div className="text-red-600 text-sm mt-2">{error}</div>}
    </form>
  );


}
