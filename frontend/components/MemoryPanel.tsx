"use client";

import { useEffect, useState } from "react";

interface Memory {
  _id?: string;
  key: string;
  value: string;
  updated_at?: string;
}

export default function MemoryPanel({ userId }: { userId: string }) {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [keyInput, setKeyInput] = useState("");
  const [valueInput, setValueInput] = useState("");
  const [error, setError] = useState("");
  const backendUrl = (process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000").replace(/\/$/, "");

  const loadMemories = async () => {
    if (!userId) return;
    try {
      const res = await fetch(`${backendUrl}/memories?user_id=${encodeURIComponent(userId)}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setMemories(data.memories || []);
    } catch (e) {
      console.error("Failed to load memories", e);
      setError("Failed to load memories");
    }
  };

  useEffect(() => {
    loadMemories();
  }, [userId]);

  const saveMemory = async () => {
    if (!keyInput.trim() || !valueInput.trim()) {
      setError("Key and value required");
      return;
    }
    try {
      setError("");
      await fetch(`${backendUrl}/memories`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, key: keyInput.trim(), value: valueInput.trim() }),
      });
      setKeyInput("");
      setValueInput("");
      loadMemories();
    } catch (e) {
      setError("Failed to save memory");
    }
  };

  const deleteMemory = async (key: string) => {
    try {
      await fetch(`${backendUrl}/memories/${encodeURIComponent(key)}?user_id=${encodeURIComponent(userId)}`, {
        method: "DELETE",
      });
      loadMemories();
    } catch (e) {
      setError("Failed to delete memory");
    }
  };

  return (
    <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-4 space-y-3 text-sm">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-wide text-gray-500">Memories</p>
          <h3 className="text-sm font-semibold text-gray-800">User context</h3>
        </div>
        <button
          onClick={loadMemories}
          className="text-xs text-blue-600 hover:text-blue-800"
          aria-label="Refresh memories"
        >
          Refresh
        </button>
      </div>
      <div className="space-y-2">
        <input
          value={keyInput}
          onChange={(e) => setKeyInput(e.target.value)}
          placeholder="Title / key"
          className="w-full px-3 py-2 rounded-lg bg-gray-50 text-gray-800 border border-gray-200 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <textarea
          value={valueInput}
          onChange={(e) => setValueInput(e.target.value)}
          placeholder="What should I remember?"
          rows={3}
          className="w-full px-3 py-2 rounded-lg bg-gray-50 text-gray-800 border border-gray-200 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          onClick={saveMemory}
          className="w-full py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white text-xs font-semibold"
        >
          Save Memory
        </button>
      </div>
      {error && <div className="text-xs text-red-500">{error}</div>}
      <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
        {memories.length === 0 ? (
          <div className="text-gray-400 text-xs">No memories yet.</div>
        ) : (
          memories.map((m) => (
            <div key={`${m.key}-${m.updated_at || ""}`} className="bg-gray-50 border border-gray-200 rounded-lg p-2.5 space-y-1">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-gray-800 text-xs">{m.key}</span>
                <button
                  onClick={() => deleteMemory(m.key)}
                  className="text-gray-400 hover:text-red-500 text-xs"
                  aria-label="Delete memory"
                >
                  ✕
                </button>
              </div>
              <p className="text-gray-700 text-xs whitespace-pre-wrap break-words">{m.value}</p>
              {m.updated_at && (
                <p className="text-[10px] text-gray-500">
                  {new Date(m.updated_at).toLocaleString()}
                </p>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
