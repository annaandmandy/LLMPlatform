export interface ClientModelConfig {
  id: string;
  name: string;
  provider: string;
}

export const DEFAULT_MODELS: ClientModelConfig[] = [
  { id: "gpt-4o-mini-search-preview", name: "GPT-4o mini", provider: "openai" },
  { id: "gpt-4o-search-preview", name: "GPT-4o", provider: "openai" },
  { id: "gpt-5-search-api", name: "GPT-5", provider: "openai" },
  { id: "x-ai/grok-3-mini:online", name: "Grok 3 mini", provider: "openrouter" },
  { id: "perplexity/sonar:online", name: "Perplexity Sonar", provider: "openrouter" },
  { id: "claude-sonnet-4-5-20250929", name: "Claude 4.5 Sonnet", provider: "anthropic" },
  { id: "gemini-2.5-flash", name: "Gemini 2.5 Flash", provider: "google" }
];

export const DEFAULT_MODEL_ID = DEFAULT_MODELS[0]?.id ?? "gpt-4o-mini-search-preview";
