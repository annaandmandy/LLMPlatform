# LLMPlatform Updates

## Latest Changes (November 2024)

### Memory System Implementation

#### Session Summaries
- **Automatic summarization** every 10 message pairs
- Two generation methods:
  - **LLM-based**: Uses gpt-4o-mini to generate 4-6 bullet points
  - **Rule-based fallback**: Extracts Q&A pairs if LLM fails
- Stored in MongoDB `summaries` collection
- Retrieved and injected into prompts for context continuity

#### Semantic Search (RAG)
- **Embedding model**: OpenAI `text-embedding-3-small` (1536 dimensions)
- **Similarity metric**: Cosine similarity with 0.45 threshold
- **Top-K retrieval**: Default 8 similar messages
- **Cross-session lookup**: Extends search to user's other sessions when current session has <50 vectors
- Async storage to avoid blocking responses

#### User Memory Store
- Persistent key/value facts per user
- Up to 8 most recent memories injected into prompts
- Token-aware with `tokenCount` field

---

### Frontend UI Improvements

#### Model Selector
- Dropdown now opens **upward** (above input)
- **Click-outside detection** with proper ref container
- Shows model name and provider
- Available models:
  - GPT-4o mini, GPT-4o, GPT-5 (OpenAI)
  - Grok 3 mini, Perplexity Sonar (OpenRouter)
  - Claude 4.5 Sonnet (Anthropic)
  - Gemini 2.5 Flash (Google)

#### Loading/Thinking Indicator
- **Dynamic thinking text** shows actual query or search status
- Product queries display: "Searching for [query]..."
- Non-product queries display: truncated query text
- Three-dot bounce animation with staggered delays
- Single-row layout with `whitespace-nowrap` and `shrink-0`

#### Markdown Rendering Fixes
- Removed `prose prose-sm` class conflicts
- Fixed bullet points "changing lines" issue
- Added `[&>li>p]:inline [&>li>p]:m-0` to handle nested paragraphs in list items
- Proper handling for:
  - Headers (h1, h2, h3)
  - Ordered and unordered lists
  - Code blocks and inline code
  - Strong/bold text
  - Images and links
- `normalizeMarkdown()` function adds proper spacing before lists

---

### Backend Agent System

#### Memory Agent (`memory_agent.py`)
- **Actions**: `retrieve`, `store_embedding`, `summarize`, `context_bundle`
- Manages vector storage, summary generation, and context retrieval
- Configuration: `summary_interval` (default: 10)

#### Writer Agent (`writer_agent.py`)
- Receives `memory_context` from Memory Agent
- `_build_prompt()` assembles all context with truncation limits:
  - History: 10 items, 200 chars
  - Summaries: 3 items, 240 chars
  - Memories: 5 items
  - Similar messages: 4 items, 200 chars
  - Recent turns: 6 items, 180 chars

#### Product Agent (`product_agent.py`)
- Extracts product mentions from LLM responses
- LLM-based extraction using gpt-4o-mini with category inference
- Regex fallback for pattern matching
- Google Shopping search via SerpAPI

---

### API Changes

#### `/query` Endpoint
- Added `use_memory` parameter (default: true)
- Response includes `memory_context` bundle
- Async embedding storage after response
- Summary generation triggered at intervals

#### Response Schema
```python
{
  "response": str,
  "citations": List[Dict],
  "memory_context": {
    "context": [...],
    "recent_messages": [...],
    "summaries": [...],
    "memories": [...]
  },
  "intent": str,
  "agents_used": List[str],
  "product_cards": List[Dict],
  "need_memory": bool,
  "memory_reason": str
}
```

---

### Bug Fixes

- Fixed git pack index corruption from macOS AppleDouble (`._*`) files
- Fixed TypeScript `Message` interface mismatch between components
- Fixed JSX syntax error in `renderMarkdown()` call
- Fixed loading dots wrapping to next line
- Fixed markdown list item line breaks

---

### Technical Details

#### MongoDB Collections
| Collection | Purpose |
|------------|---------|
| `vectors` | Message embeddings (1536-dim) |
| `summaries` | Session summaries (array per session) |
| `memories` | User facts (key/value) |
| `sessions` | Raw events (prompts, responses, clicks) |

#### Embedding Pipeline
1. User sends message
2. LLM generates response
3. Both messages embedded async
4. Stored in `vectors` collection
5. Retrieved via cosine similarity search

#### Summary Pipeline
1. Count message pairs in session
2. If `count % 10 == 0`: trigger summary
3. Fetch last 12 messages
4. Generate via LLM or rule-based
5. Append to session's summary document

---

### Configuration

#### Environment Variables
- `OPENAI_API_KEY` - Required for embeddings/summaries
- `SERPAPI_KEY` - For product search
- `USE_LLM_INTENT` - Enable embedding-based intent detection
- `NEXT_PUBLIC_BACKEND_URL` - Backend API URL

#### Frontend Constants
- `PRODUCT_KEYWORDS` - Regex for product intent detection
- `MAX_IMAGE_DIMENSION` - 1200px
- `MAX_IMAGE_BYTES` - 1.5MB

---

## File Structure

```
LLMPlatform/
├── fastapi-llm-logger/
│   ├── agents/
│   │   ├── memory_agent.py      # Memory retrieval & storage
│   │   ├── writer_agent.py      # Prompt building & LLM calls
│   │   ├── product_agent.py     # Product extraction & search
│   │   └── coordinator_agent.py # Intent routing
│   ├── utils/
│   │   └── embeddings.py        # OpenAI embedding utilities
│   ├── config/
│   │   └── provider_prompts.json
│   └── main.py                  # FastAPI endpoints
├── llm-frontend/
│   ├── app/
│   │   └── page.tsx             # Main page with state
│   └── components/
│       ├── QueryBox.tsx         # Input with model selector
│       ├── MessageHistory.tsx   # Message display & markdown
│       └── ProductCard.tsx      # Product card component
├── README_MEMORY.md             # Memory system documentation
└── UPDATES.md                   # This file
```
