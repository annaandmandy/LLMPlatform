# Observability & Monitoring

## Database Collections & Schemas

The system uses MongoDB Atlas with the following collections:

### 1. Queries (`queries`)
Primary storage for Q&A interactions. This collection is indexed for Vector Search.

| Field | Type | Description |
|-------|------|-------------|
| `_id` | ObjectId | Unique ID |
| `user_id` | String | User Identifier |
| `session_id` | String | Session Identifier |
| `query` | String | User's question text |
| `response` | String | LLM's generated answer |
| `embedding` | Array[Float] | 1536-dim vector for semantic search |
| `model_provider` | String | e.g., "openai", "anthropic" |
| `model_name` | String | e.g., "gpt-4o-mini" |
| `timestamp` | Date | When the query occurred |
| `latency_ms` | Float | Generation time in milliseconds |
| `tokens` | Object | Token usage `{prompt: 10, completion: 20}` |
| `citations` | Array | List of RAG sources used |
| `intent` | String | Detected intent (e.g., "shopping") |
| `agents_used` | Array[String] | Agents involved (e.g., "ShoppingAgent") |

### 2. Sessions (`sessions`)
Tracks user session lifecycles and fine-grained UX events.

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | String | Unique Session ID |
| `user_id` | String | User Identifier |
| `status` | String | "active" or "ended" |
| `start_time` | Date | Session start timestamp |
| `end_time` | Date | Session end timestamp |
| `environment` | Object | Device info `{browser: "Chrome", os: "Mac"}` |
| `events` | Array[Object] | Stream of UX events (see below) |

**Event Object Structure:**
```json
{
  "t": 1709232000000,      // Timestamp (ms)
  "type": "click",         // start, click, scroll, hover
  "data": {                // Event-specific data
    "target": "submit-btn",
    "scrollY": 500
  }
}
```

### 3. Products (`products`)
Cache for product information to avoid re-fetching from external APIs. Currently not used, but for future product list storage, could be used for ads experiment and testing response.

| Field | Type | Description |
|-------|------|-------------|
| `product_id` | String | Unique Product ID |
| `name` | String | Product Name |
| `description` | String | Product Description |
| `price` | String | Price string (e.g. "$19.99") |
| `image_url` | String | URL to product image |
| `url` | String | Link to purchase page |
| `rating` | Float | Rating count or score |

### 4. Summaries (`summaries`)
Stores condensed conversation history for long-term memory. Every 10 pairs of Q&A, the summary function would be called and save a summary for the conversation.

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | String | Session Identifier |
| `user_id` | String | User Identifier |
| `summaries` | Array[Object] | List of summary entries |
| `created_at` | Date | Creation timestamp |

**Summary Entry Structure:**
```json
{
  "text": "User asked about headphones...",
  "message_count": 4,
  "model": "gpt-4o-mini",
  "t": "2024-03-01T12:00:00"
}
```

### 5. Files (`files`)
Metadata for user-uploaded files. Currently we have not implemented S3 storage, so no files have been saved, and also we only have photo reading(vision agent) function yet. Could be our next step if needed.

| Field | Type | Description |
|-------|------|-------------|
| `user_id` | String | Uploader ID |
| `filename` | String | Original filename |
| `file_path` | String | Storage path (local/S3) |
| `content_type` | String | MIME type (e.g., "application/pdf") |
| `size_bytes` | Int | File size |
| `purpose` | String | e.g., "attachment" |
| `created_at` | Date | Upload timestamp | 
