# Multi-Agent LLM Platform Architecture

## 🎯 Overview

This document describes the multi-agent architecture upgrade for the LLM Brand Experiment platform. The system now features intelligent intent detection, RAG-based memory retrieval, real-time product search from Google Shopping, and context-aware response generation.

## 🏗️ Architecture Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                         User Query                            │
└──────────────────────┬───────────────────────────────────────┘
                       ↓
          ┌────────────────────────────┐
          │   CoordinatorAgent         │
          │   (Intent Detection)       │
          └────────────┬───────────────┘
                       ↓
        ┌──────────────┼──────────────┐
        ↓              ↓              ↓
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ MemoryAgent  │ │ WriterAgent  │ │ ProductAgent │
│ (RAG + Emb)  │ │ (LLM Calls)  │ │ (Google Shop)│
└──────────────┘ └──────────────┘ └──────────────┘
        │              │              │
        └──────────────┼──────────────┘
                       ↓
          ┌────────────────────────────┐
          │   Final Response +         │
          │   Product Cards            │
          └────────────────────────────┘
```

## 📦 Components

### Backend Agents

#### 1. **Base Agent** (`agents/base_agent.py`)
- Abstract base class for all agents
- Provides logging, error handling, and execution tracking
- Automatically logs to `agent_logs` collection
- Tracks latency, execution count, and status

#### 2. **Coordinator Agent** (`agents/coordinator.py`)
- **Role**: Routes requests to appropriate agents based on detected intent
- **Intents**:
  - `product_search`: User wants to find/buy products
  - `summarize`: User requests conversation summary
  - `retrieve_memory`: User references past conversations
  - `general`: Standard conversation
- **Flow**:
  - Detects intent using keyword patterns
  - Routes to Memory, Product, or Writer agents
  - Combines results and returns final response

#### 3. **Memory Agent** (`agents/memory_agent.py`)
- **Role**: Manages conversation memory and context retrieval
- **Features**:
  - **Embeddings**: Stores message embeddings using sentence-transformers
  - **RAG Retrieval**: Finds semantically similar past messages
  - **Summarization**: Creates session summaries every 10 turns
- **Collections Used**:
  - `vectors`: Stores embeddings for semantic search
  - `summaries`: Stores periodic conversation summaries

#### 4. **Product Agent** (`agents/product_agent.py`)
- **Role**: Extracts product mentions from LLM responses and fetches real products
- **Flow**:
  1. LLM generates response (e.g., "I recommend the Sony WH-1000XM5 headphones")
  2. ProductAgent extracts "Sony WH-1000XM5" using regex patterns
  3. Searches Google Shopping via SerpAPI
  4. Returns real product cards with images, prices, and purchase links
- **API**: Google Shopping via SerpAPI
- **Output**: Product cards with title, price, image, seller, rating, reviews

#### 5. **Writer Agent** (`agents/writer_agent.py`)
- **Role**: Generates final responses using LLM with enriched context
- **Features**:
  - Integrates with existing LLM providers (OpenAI, Anthropic, Google, OpenRouter)
  - Enriches prompts with memory context and conversation history
  - Returns responses with citations

### Utilities

#### **Intent Classifier** (`utils/intent_classifier.py`)
- Hybrid keyword + pattern-based intent detection
- Configurable confidence scores
- Extensible for LLM-based classification

#### **Embeddings** (`utils/embeddings.py`)
- Uses `sentence-transformers` (all-MiniLM-L6-v2)
- 384-dimensional embeddings
- Cosine similarity for semantic search
- Batch processing support

### Frontend Components

#### **ProductCard** (`components/ProductCard.tsx`)
- Displays product information in a clean card layout
- Shows: image, title, price, rating, reviews, seller
- Tags for special offers and delivery info
- Click tracking for analytics

#### **MessageHistory** (`components/MessageHistory.tsx`)
- Renders chat messages with markdown support
- Toggleable citations
- **NEW**: Renders product cards below assistant messages
- Responsive grid layout (1 column mobile, 2 columns desktop)

#### **QueryBox** (`components/QueryBox.tsx`)
- **NEW**: Sends last 10 messages as conversation history
- Supports all 7 LLM models
- Handles product_cards in response

## 🔄 Request/Response Flow

### Example: Product Search Query

**User**: "What's a good noise-cancelling headphone?"

1. **Query Submission**:
```typescript
POST /query
{
  "query": "What's a good noise-cancelling headphone?",
  "user_id": "uuid",
  "session_id": "uuid",
  "model_name": "gpt-4o-mini-search-preview",
  "model_provider": "openai",
  "history": [...]  // Last 10 messages
}
```

2. **Coordinator Detection**:
- Intent: `product_search` (confidence: 0.65)
- Routes to: WriterAgent → ProductAgent

3. **WriterAgent Response**:
```
"I recommend the Sony WH-1000XM5 wireless headphones. They offer
industry-leading noise cancellation, 30-hour battery life..."
```

4. **ProductAgent Extraction**:
- Extracts: "Sony WH-1000XM5"
- Searches Google Shopping via SerpAPI
- Finds real products with prices and links

5. **Final Response**:
```json
{
  "response": "I recommend the Sony WH-1000XM5...",
  "citations": [...],
  "product_cards": [
    {
      "title": "Sony WH-1000XM5 Wireless Noise Cancelling Headphones",
      "price": "$398.00",
      "image": "https://...",
      "url": "https://amazon.com/...",
      "seller": "Amazon",
      "rating": 4.6,
      "reviews_count": 8200
    }
  ],
  "intent": "product_search",
  "agents_used": ["CoordinatorAgent", "WriterAgent", "ProductAgent"]
}
```

## 🗄️ Database Schema

### New Collections

#### `vectors`
```javascript
{
  session_id: string,
  message_index: number,
  role: "user" | "assistant",
  content: string,
  embedding: float[384],  // sentence-transformers embedding
  timestamp: datetime
}
```

#### `summaries`
```javascript
{
  session_id: string,
  summaries: [{
    t: datetime,
    text: string,
    message_count: number
  }],
  created_at: datetime
}
```

#### `agent_logs`
```javascript
{
  agent_name: string,
  session_id: string,
  user_id: string,
  timestamp: datetime,
  latency_ms: float,
  status: "success" | "error",
  input_summary: string,
  output_summary: string,
  execution_count: number
}
```

### Existing Collections (Unchanged)

- **`queries`**: Query/response logging
- **`sessions`**: Session-based event tracking
- **`events`**: Legacy event logging

## 🔑 Configuration

### Environment Variables

#### Backend (`.env` in `fastapi-llm-logger/`)
```bash
# Existing
MONGODB_URI=mongodb+srv://...
MONGO_DB=llm_experiment
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
OPENROUTER_API_KEY=sk-or-...

# NEW for Multi-Agent
SERPAPI_KEY=your_serpapi_key_here
```

#### Frontend (`.env.local` in `llm-frontend/`)
```bash
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

### Dependencies

#### Backend (`requirements.txt`)
```
# Existing dependencies...

# NEW: Multi-Agent System
sentence-transformers==2.2.2
numpy==1.26.4
scikit-learn==1.3.2
```

Install with:
```bash
cd fastapi-llm-logger
pip install -r requirements.txt
```

## 🚀 Getting Started

### 1. Install Dependencies

**Backend**:
```bash
cd fastapi-llm-logger
pip install -r requirements.txt
```

**Frontend**:
```bash
cd llm-frontend
npm install
```

### 2. Configure Environment Variables

Add `SERPAPI_KEY` to `fastapi-llm-logger/.env`:
```bash
SERPAPI_KEY=your_key_from_serpapi.com
```

Get your free key at: https://serpapi.com/

### 3. Start Services

**Backend**:
```bash
cd fastapi-llm-logger
uvicorn main:app --reload --port 8000
```

**Frontend**:
```bash
cd llm-frontend
npm run dev
```

### 4. Test the System

Try these queries to test different intents:

- **Product Search**: "I need noise-cancelling headphones"
- **Memory Retrieval**: "What did we discuss earlier?"
- **Summarize**: "Summarize our conversation"
- **General**: "Tell me about machine learning"

## 📊 Intent Detection Examples

| Query | Detected Intent | Agents Used |
|-------|----------------|-------------|
| "I want to buy a laptop" | `product_search` | Writer → Product |
| "What did I ask about yesterday?" | `retrieve_memory` | Memory → Writer |
| "Summarize our chat" | `summarize` | Memory |
| "Explain quantum computing" | `general` | Writer |

## 🎨 Product Card Display

Product cards appear below the assistant's response when products are mentioned:

```
┌─────────────────────────────────────────┐
│ [Assistant Message]                     │
│ "I recommend the Sony WH-1000XM5..."    │
└─────────────────────────────────────────┘

🛍️ Related Products
┌──────────────────┐ ┌──────────────────┐
│ [Image]          │ │ [Image]          │
│ Sony WH-1000XM5  │ │ Sony WH-1000XM4  │
│ $398.00          │ │ $278.00          │
│ ★ 4.6 (8.2k)     │ │ ★ 4.7 (12k)      │
│ from Amazon      │ │ from Best Buy    │
└──────────────────┘ └──────────────────┘
```

## 🔍 Monitoring & Debugging

### Agent Logs
All agent executions are logged to the `agent_logs` collection:
```javascript
{
  "agent_name": "ProductAgent",
  "latency_ms": 450.2,
  "status": "success",
  "input_summary": "Extracting product mentions from...",
  "execution_count": 42
}
```

### Backend Logs
Check terminal for real-time agent activity:
```
INFO: 🤖 Using multi-agent system
INFO: Intent detected: product_search (confidence: 0.65)
INFO: Searching Google Shopping for: Sony WH-1000XM5
INFO: Found 3 products for 'Sony WH-1000XM5'
```

## 🎯 Future Enhancements

- [ ] LLM-based intent classification for better accuracy
- [ ] Expand product patterns to detect more product types
- [ ] Multi-turn conversation context in WriterAgent
- [ ] Automatic summarization trigger
- [ ] LangGraph visualization
- [ ] Analytics dashboard for agent performance
- [ ] Support for more product APIs (Amazon, eBay)
- [ ] User preference learning in MemoryAgent

## 📝 API Reference

### POST `/query`
Main endpoint for chat queries (multi-agent enabled).

**Request**:
```json
{
  "user_id": "string",
  "session_id": "string",
  "query": "string",
  "model_name": "string",
  "model_provider": "string",
  "history": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}
```

**Response**:
```json
{
  "response": "string",
  "citations": [...],
  "product_cards": [...],
  "intent": "string",
  "agents_used": ["string"]
}
```

### GET `/search/products?query=...&max_results=10`
Direct product search endpoint.

**Response**:
```json
{
  "products": [...],
  "total": number,
  "query": "string"
}
```

## 🤝 Contributing

When adding new agents:
1. Extend `BaseAgent` class
2. Implement `async execute()` method
3. Register in `CoordinatorAgent`
4. Update intent patterns if needed
5. Test with various queries

## 📄 License

This project is part of the LLM Brand Experiment research platform.

---

**Built with**: FastAPI, Next.js, MongoDB, SerpAPI, sentence-transformers, OpenAI, Anthropic, Google AI, OpenRouter
