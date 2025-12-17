# 🛠️ Configuration & Adjustment Guide

This guide helps you tweak the behavior of the **LLM Platform** without modifying the core logic. You can control how models speak, how products are searched, and how intents are detected.

---

## 1. 🤖 AI Personas & Prompts (Change How It Speaks)

You can customize the "personality" and system instructions for each AI model provider.

### **Main System Prompts**
- **File**: `fastapi-llm-logger/config/provider_prompts.json`
- **What it does**: Defines the system prompt for OpenAI, Anthropic, Google, etc.
- **How to adjust**: Edit the value for each provider key.
  ```json
  {
    "openai": "You are ChatGPT, a helpful assistant...",
    "anthropic": "You are Claude, a careful and thoughtul assistant...",
    "openrouter_grok": "You are Grok, a witty assistant..."
  }
  ```
- **Supported Keys**: `openai`, `anthropic`, `google`, `openrouter_perplexity`, `openrouter_grok`.

### **Shopping Mode Interview**
- **File**: `fastapi-llm-logger/agents/shopping_agent.py` (Search for `system_prompt = ...`)
- **What it does**: Controls how the AI acts during the "Shopping Mode" interview (e.g., how many questions to ask, tone).
- **Key Params to Tweaks**:
  - "3 rounds of diagnostic questions" (Change `3` to `5` for deeper interviews).
  - "MAX 5 WORDS PER OPTION" (Adjust formatting constraints).

### **Product Extraction Logic**
- **File**: `fastapi-llm-logger/agents/product_agent.py` (Search for `EXTRACTION_SYSTEM_PROMPT`)
- **What it does**: Tells the AI how to find product names in a generic text response.
- **Why change**: If it misses products or extracts irrelevant nouns.

---

## 2. 🧠 Intent Detection (Change How It Understands)

Control when the system decides to switch to "Shopping Mode" or "Product Search" versus "General Chat".

### **Keywords & Rules**
- **File**: `fastapi-llm-logger/config/intent_keywords.json` (If using keyword mode)
- **File**: `fastapi-llm-logger/utils/intent_classifier.py`
  - **Variable**: `INTENT_DEFINITIONS`
  - **What it does**: Descriptions used for **Semantic Matching** (if `USE_LLM_INTENT=true`).
  - **How to adjust**: Change the description of `product_search` to be more specific or broad.

### **Confidence Thresholds**
- **File**: `fastapi-llm-logger/utils/intent_classifier.py`
  - **Variable**: `confidence` calculation in `classify()`
  - **What it does**: Determines how strictly it matches keywords.

---

## 3. 🛒 Product Search Settings (Change Results)

Customize how many products are shown and where they come from.

### **Search Parameters**
- **File**: `fastapi-llm-logger/agents/product_agent.py`
  - **Variable**: `request.get("max_results", 1)`
  - **What it does**: Controls how many product cards are shown per extraction.
  - **Default**: `1` (to keep UI clean).
- **Timeout**: `PRODUCT_SEARCH_TIMEOUT` (Default 10s) in `.env` or code.

---

## 4. 🎨 Frontend Styling (Change Look & Feel)

Quick UI tweaks without rewriting components.

### **Global Theme**
- **File**: `llm-frontend/app/globals.css`
  - **What it does**: CSS variables for `background`, `foreground`, `primary` colors.

### **Tailwind Config**
- **File**: `llm-frontend/tailwind.config.ts`
  - **What it does**: Define custom animations (like `pulse`, `shimmer`) and color palettes.

---

## 5. 🔑 Environment Variables (.env)

Critical switches for external services.

### **Backend (`fastapi-llm-logger/.env`)**
| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | Enabled OpenAI models (GPT-4o, etc) |
| `ANTHROPIC_API_KEY` | Enables Claude 3.5 Sonnet |
| `GOOGLE_API_KEY` | Enables Gemini |
| `SERPAPI_KEY` | **Required** for Product Search & Cards to work |
| `USE_LLM_INTENT` | Set to `true` to use AI for intent (slower but smarter) vs Keyword (fast) |

### **Frontend (`llm-frontend/.env.local`)**
| Variable | Purpose |
|----------|---------|
| `NEXT_PUBLIC_BACKEND_URL` | URL of your Python backend (e.g. `http://localhost:8000`) |
