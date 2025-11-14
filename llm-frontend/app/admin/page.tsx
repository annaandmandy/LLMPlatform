"use client";

import { useEffect, useMemo, useState } from "react";
import { DEFAULT_MODELS } from "@/config/defaultClientConfig";

interface ModelConfig {
  id: string;
  name: string;
  provider: string;
}

interface NumericConfig {
  memory_similarity_threshold: number;
  history_fallback_pairs: number;
  max_history_messages: number;
  product_mentions_limit: number;
  serp_results_per_product: number;
}

interface AdminConfig {
  intents: Record<string, string>;
  prompts: Record<string, string>;
  numeric: NumericConfig;
  available_models: ModelConfig[];
}

const ADMIN_PASSWORD = process.env.NEXT_PUBLIC_ADMIN_PASSWORD || "1111";

export default function AdminPage() {
  const [authorized, setAuthorized] = useState(false);
  const [authChecked, setAuthChecked] = useState(false);
  const [config, setConfig] = useState<AdminConfig | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [statusMessage, setStatusMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [newIntent, setNewIntent] = useState({ name: "", description: "" });
  const [newModel, setNewModel] = useState<ModelConfig>({ id: "", name: "", provider: "" });

  const backendUrl = useMemo(
    () => (process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000").replace(/\/$/, ""),
    []
  );

  useEffect(() => {
    const attemptAuth = () => {
      const attempt = window.prompt("Enter admin password");
      if (attempt === ADMIN_PASSWORD) {
        setAuthorized(true);
      } else {
        setAuthorized(false);
      }
      setAuthChecked(true);
    };

    attemptAuth();
  }, []);

  useEffect(() => {
    if (!authorized) return;
    const fetchConfig = async () => {
      try {
        setLoading(true);
        setStatusMessage(null);
        const res = await fetch(`${backendUrl}/admin/config`);
        if (!res.ok) {
          throw new Error(`Failed to fetch config (${res.status})`);
        }
        const data = (await res.json()) as AdminConfig;
        setConfig(data);
      } catch (err) {
        console.error(err);
        setStatusMessage({ type: "error", text: err instanceof Error ? err.message : "Failed to fetch config" });
      } finally {
        setLoading(false);
      }
    };
    fetchConfig();
  }, [authorized, backendUrl]);

  const handleIntentDescriptionChange = (intent: string, value: string) => {
    setConfig((prev) => {
      if (!prev) return prev;
      return { ...prev, intents: { ...prev.intents, [intent]: value } };
    });
  };

  const handlePromptChange = (key: string, value: string) => {
    setConfig((prev) => {
      if (!prev) return prev;
      return { ...prev, prompts: { ...prev.prompts, [key]: value } };
    });
  };

  const handleNumericChange = (key: keyof NumericConfig, value: number) => {
    setConfig((prev) => {
      if (!prev) return prev;
      return { ...prev, numeric: { ...prev.numeric, [key]: value } };
    });
  };

  const handleModelChange = (index: number, key: keyof ModelConfig, value: string) => {
    setConfig((prev) => {
      if (!prev) return prev;
      const updated = [...prev.available_models];
      updated[index] = { ...updated[index], [key]: value };
      return { ...prev, available_models: updated };
    });
  };

  const handleRemoveIntent = (intent: string) => {
    if (intent === "general") return;
    setConfig((prev) => {
      if (!prev) return prev;
      const nextIntents = { ...prev.intents };
      delete nextIntents[intent];
      const nextPrompts = { ...prev.prompts };
      delete nextPrompts[intent];
      return { ...prev, intents: nextIntents, prompts: nextPrompts };
    });
  };

  const handleRemoveModel = (index: number) => {
    setConfig((prev) => {
      if (!prev) return prev;
      const updated = prev.available_models.filter((_, idx) => idx !== index);
      return { ...prev, available_models: updated };
    });
  };

  const handleAddIntent = () => {
    if (!config) return;
    const rawName = newIntent.name.trim().toLowerCase().replace(/\s+/g, "_");
    const description = newIntent.description.trim();
    if (!rawName || rawName === "general" || !description) {
      setStatusMessage({ type: "error", text: "Intent name and description are required (general can't be added)." });
      return;
    }
    if (config.intents[rawName]) {
      setStatusMessage({ type: "error", text: "Intent already exists." });
      return;
    }

    const basePrompt = config.prompts.general || "Answer the user directly.";
    setConfig({
      ...config,
      intents: { ...config.intents, [rawName]: description },
      prompts: { ...config.prompts, [rawName]: basePrompt },
    });
    setNewIntent({ name: "", description: "" });
    setStatusMessage(null);
  };

  const handleAddModel = () => {
    if (!config) return;
    const { id, name, provider } = newModel;
    if (!id.trim() || !name.trim() || !provider.trim()) {
      setStatusMessage({ type: "error", text: "Model id, name, and provider are required." });
      return;
    }
    if (config.available_models.find((m) => m.id === id.trim())) {
      setStatusMessage({ type: "error", text: "Model id already exists." });
      return;
    }
    setConfig({
      ...config,
      available_models: [...config.available_models, { id: id.trim(), name: name.trim(), provider: provider.trim() }],
    });
    setNewModel({ id: "", name: "", provider: "" });
    setStatusMessage(null);
  };

  const sortedIntents = config
    ? Object.entries(config.intents).sort(([a], [b]) => {
        if (a === "general") return -1;
        if (b === "general") return 1;
        return a.localeCompare(b);
      })
    : [];

  const retryAuth = () => {
    setAuthChecked(false);
    const attempt = window.prompt("Enter admin password");
    if (attempt === ADMIN_PASSWORD) {
      setAuthorized(true);
    } else {
      setAuthorized(false);
    }
    setAuthChecked(true);
  };

  const validateBeforeSave = () => {
    if (!config) return "No config loaded.";
    if (!config.prompts.system?.trim()) return "System prompt cannot be empty.";
    for (const [intent, description] of Object.entries(config.intents)) {
      if (!description.trim()) return `Description for ${intent} cannot be empty.`;
      if (!config.prompts[intent]?.trim()) return `Prompt for ${intent} cannot be empty.`;
    }
    if (!config.available_models.length) return "At least one model must be configured.";
    for (const model of config.available_models) {
      if (!model.id.trim() || !model.name.trim() || !model.provider.trim()) {
        return "All models must have id, name, and provider.";
      }
    }
    if (config.numeric.serp_results_per_product < 1) return "SERP product count must be at least 1.";
    return null;
  };

  const handleSave = async () => {
    const validationError = validateBeforeSave();
    if (validationError) {
      setStatusMessage({ type: "error", text: validationError });
      return;
    }
    try {
      setSaving(true);
      setStatusMessage(null);
      const res = await fetch(`${backendUrl}/admin/config`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
      });
      if (!res.ok) {
        throw new Error(`Failed to save config (${res.status})`);
      }
      const data = (await res.json()) as AdminConfig;
      setConfig(data);
      setStatusMessage({ type: "success", text: "Configuration updated." });
    } catch (err) {
      console.error(err);
      setStatusMessage({ type: "error", text: err instanceof Error ? err.message : "Failed to save config" });
    } finally {
      setSaving(false);
    }
  };

  if (!authChecked) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100 text-gray-700">
        <p>Checking admin access…</p>
      </div>
    );
  }

  if (!authorized) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-gray-100 text-gray-800 gap-4">
        <p className="text-lg font-semibold">Access denied. Incorrect password.</p>
        <button
          onClick={retryAuth}
          className="px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700 transition-colors"
        >
          Try Again
        </button>
      </div>
    );
  }

  if (loading || !config) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100 text-gray-700">
        <p>Loading admin controls…</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 p-6">
      <div className="max-w-5xl mx-auto space-y-8">
        <header className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Admin Control Panel</h1>
            <p className="text-gray-600">Adjust intents, prompts, model availability, and SERP knobs.</p>
          </div>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {saving ? "Saving…" : "Save Changes"}
          </button>
        </header>

        {statusMessage && (
          <div
            className={`rounded-md px-4 py-3 ${
              statusMessage.type === "success" ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
            }`}
          >
            {statusMessage.text}
          </div>
        )}

        <section className="bg-white rounded-xl shadow p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">Intents</h2>
            <span className="text-sm text-gray-500">General intent cannot be removed.</span>
          </div>
          <div className="space-y-4">
            {sortedIntents.map(([intent, description]) => (
              <div key={intent} className="border rounded-lg p-4 space-y-3 bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="font-semibold capitalize">{intent.replace(/_/g, " ")}</div>
                  {intent !== "general" && (
                    <button
                      onClick={() => handleRemoveIntent(intent)}
                      className="text-sm text-red-600 hover:text-red-700"
                    >
                      Remove
                    </button>
                  )}
                </div>
                <input
                  type="text"
                  value={description}
                  onChange={(e) => handleIntentDescriptionChange(intent, e.target.value)}
                  className="w-full border rounded-md px-3 py-2"
                />
              </div>
            ))}
          </div>

          <div className="border-t pt-4">
            <h3 className="font-semibold mb-2">Add Intent</h3>
            <div className="grid gap-3 md:grid-cols-2">
              <input
                type="text"
                placeholder="intent key (e.g., checkout_support)"
                value={newIntent.name}
                onChange={(e) => setNewIntent((prev) => ({ ...prev, name: e.target.value }))}
                className="border rounded-md px-3 py-2"
              />
              <input
                type="text"
                placeholder="Description"
                value={newIntent.description}
                onChange={(e) => setNewIntent((prev) => ({ ...prev, description: e.target.value }))}
                className="border rounded-md px-3 py-2"
              />
            </div>
            <button
              onClick={handleAddIntent}
              className="mt-3 px-4 py-2 bg-gray-900 text-white rounded-md hover:bg-black"
            >
              Add Intent
            </button>
          </div>
        </section>

        <section className="bg-white rounded-xl shadow p-5 space-y-4">
          <h2 className="text-xl font-semibold">Prompts</h2>
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-600 mb-1">System Prompt</label>
              <textarea
                value={config.prompts.system || ""}
                onChange={(e) => handlePromptChange("system", e.target.value)}
                rows={3}
                className="w-full border rounded-md px-3 py-2"
              />
            </div>
            {sortedIntents.map(([intent]) => (
              <div key={intent}>
                <label className="block text-sm font-medium text-gray-600 mb-1">
                  {intent === "general" ? "General Prompt" : `${intent.replace(/_/g, " ")} Prompt`}
                </label>
                <textarea
                  value={config.prompts[intent] || ""}
                  onChange={(e) => handlePromptChange(intent, e.target.value)}
                  rows={4}
                  className="w-full border rounded-md px-3 py-2"
                />
              </div>
            ))}
          </div>
        </section>

        <section className="bg-white rounded-xl shadow p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">Numerics & SERP controls</h2>
            <div className="text-sm text-gray-500">
              Google SERP products per search:{" "}
              <span className="font-semibold text-gray-900">{config.numeric.serp_results_per_product}</span>
            </div>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <label className="flex flex-col text-sm text-gray-600">
              Memory similarity threshold
              <input
                type="number"
                step="0.05"
                min={0}
                value={config.numeric.memory_similarity_threshold}
                onChange={(e) =>
                  handleNumericChange("memory_similarity_threshold", parseFloat(e.target.value) || 0)
                }
                className="mt-1 border rounded-md px-3 py-2"
              />
            </label>
            <label className="flex flex-col text-sm text-gray-600">
              History fallback pairs
              <input
                type="number"
                min={0}
                value={config.numeric.history_fallback_pairs}
                onChange={(e) =>
                  handleNumericChange("history_fallback_pairs", parseInt(e.target.value, 10) || 0)
                }
                className="mt-1 border rounded-md px-3 py-2"
              />
            </label>
            <label className="flex flex-col text-sm text-gray-600">
              Max history messages
              <input
                type="number"
                min={2}
                value={config.numeric.max_history_messages}
                onChange={(e) =>
                  handleNumericChange("max_history_messages", parseInt(e.target.value, 10) || 2)
                }
                className="mt-1 border rounded-md px-3 py-2"
              />
            </label>
            <label className="flex flex-col text-sm text-gray-600">
              Product mentions limit
              <input
                type="number"
                min={1}
                value={config.numeric.product_mentions_limit}
                onChange={(e) =>
                  handleNumericChange("product_mentions_limit", parseInt(e.target.value, 10) || 1)
                }
                className="mt-1 border rounded-md px-3 py-2"
              />
            </label>
            <label className="flex flex-col text-sm text-gray-600">
              SERP products per intent
              <input
                type="number"
                min={1}
                value={config.numeric.serp_results_per_product}
                onChange={(e) =>
                  handleNumericChange("serp_results_per_product", parseInt(e.target.value, 10) || 1)
                }
                className="mt-1 border rounded-md px-3 py-2"
              />
            </label>
          </div>
        </section>

        <section className="bg-white rounded-xl shadow p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">Available Models</h2>
            <p className="text-sm text-gray-500">These populate the QueryBox dropdown.</p>
          </div>
          <div className="space-y-4">
            {config.available_models.map((model, index) => (
              <div key={model.id} className="border rounded-lg p-4 grid gap-3 md:grid-cols-3">
                <input
                  type="text"
                  value={model.id}
                  onChange={(e) => handleModelChange(index, "id", e.target.value)}
                  className="border rounded-md px-3 py-2"
                  placeholder="Model id"
                />
                <input
                  type="text"
                  value={model.name}
                  onChange={(e) => handleModelChange(index, "name", e.target.value)}
                  className="border rounded-md px-3 py-2"
                  placeholder="Display name"
                />
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={model.provider}
                    onChange={(e) => handleModelChange(index, "provider", e.target.value)}
                    className="flex-1 border rounded-md px-3 py-2"
                    placeholder="Provider"
                  />
                  <button
                    onClick={() => handleRemoveModel(index)}
                    className="px-3 py-2 text-sm text-red-600 hover:text-red-700"
                  >
                    Remove
                  </button>
                </div>
              </div>
            ))}
          </div>

          <div className="border-t pt-4 space-y-3">
            <h3 className="font-semibold">Add Model</h3>
            <div className="grid gap-3 md:grid-cols-3">
              <input
                type="text"
                placeholder="Model id"
                value={newModel.id}
                onChange={(e) => setNewModel((prev) => ({ ...prev, id: e.target.value }))}
                className="border rounded-md px-3 py-2"
              />
              <input
                type="text"
                placeholder="Name"
                value={newModel.name}
                onChange={(e) => setNewModel((prev) => ({ ...prev, name: e.target.value }))}
                className="border rounded-md px-3 py-2"
              />
              <input
                type="text"
                placeholder="Provider"
                value={newModel.provider}
                onChange={(e) => setNewModel((prev) => ({ ...prev, provider: e.target.value }))}
                className="border rounded-md px-3 py-2"
              />
            </div>
            <button onClick={handleAddModel} className="px-4 py-2 bg-gray-900 text-white rounded-md hover:bg-black">
              Add Model
            </button>
          </div>
        </section>

        <footer className="text-xs text-gray-500 text-center">
          Defaults fall back to {DEFAULT_MODELS.length} launch models if backend settings are missing.
        </footer>
      </div>
    </div>
  );
}
