# Understanding Session Tracking in Your LLM Platform

## Two Types of Sessions

Your application now has **two separate session concepts**:

### 1. Chat Session (`sessionId`)
- **Purpose**: Groups related chat messages together
- **Lifecycle**: Changes when user clicks "New Chat"
- **Storage**: `sessionStorage` (per tab)
- **Used for**:
  - Displaying conversation history
  - Saving/loading chat messages
  - Organizing chat history in sidebar

### 2. Tracking Session (`trackingSessionId`)
- **Purpose**: Tracks ALL user behavior during one visit
- **Lifecycle**: Created once per page load, ends on tab close
- **Storage**: MongoDB `sessions` collection
- **Used for**:
  - Analytics and research
  - Understanding user behavior patterns
  - A/B testing between models
  - Session replay and analysis

## What Gets Tracked Automatically

When a user visits your app, the following is tracked automatically:

### On Page Load
```json
{
  "session_id": "user_xxx_1730..._abc",
  "user_id": "user_xxx",
  "model_group": "gpt-4o-mini",
  "experiment_id": "production_v1",
  "environment": {
    "device": "desktop",
    "browser": "Chrome",
    "os": "macOS",
    "viewport": { "width": 1920, "height": 1080 }
  },
  "events": []
}
```

### During User Interaction

**Scroll Events** (throttled to every 500ms):
```json
{
  "t": 1730000005000,
  "type": "scroll",
  "data": {
    "scrollY": 500,
    "speed": 100,
    "direction": "down"
  }
}
```

**Click Events** (every click):
```json
{
  "t": 1730000008000,
  "type": "click",
  "data": {
    "target": "BUTTON",
    "x": 150,
    "y": 300,
    "page_url": "/"
  }
}
```

**Text Selection**:
```json
{
  "t": 1730000010000,
  "type": "selection",
  "data": {
    "selected_text": "Machine learning is...",
    "page_url": "/"
  }
}
```

**Copy Events**:
```json
{
  "t": 1730000012000,
  "type": "copy",
  "data": {
    "selected_text": "Machine learning is..."
  }
}
```

**Activity State** (idle after 30s of no interaction):
```json
{
  "t": 1730000042000,
  "type": "activity",
  "data": {
    "activity_state": "idle"
  }
}
```

### When User Sends a Query

The `/query` endpoint in your backend **automatically** logs two events:

**Prompt Event**:
```json
{
  "t": 1730000015000,
  "type": "prompt",
  "data": {
    "text": "What is machine learning?"
  }
}
```

**Model Response Event**:
```json
{
  "t": 1730000017500,
  "type": "model_response",
  "data": {
    "text": "Machine learning is...",
    "model": "gpt-4o-mini",
    "provider": "openai",
    "latency_ms": 2500,
    "response_length": 250,
    "citations": [...]
  }
}
```

## Example User Journey

A complete tracking session might look like this:

```json
{
  "session_id": "user_abc_1730000000000_xyz",
  "user_id": "abc-123-def-456",
  "model_group": "gpt-4o-mini",
  "start_time": "2024-10-27T10:00:00Z",
  "end_time": "2024-10-27T10:15:30Z",
  "environment": { ... },
  "events": [
    // User arrives (automatic)
    { "t": 1730000000000, "type": "activity", "data": { "activity_state": "active" }},

    // User scrolls down the page
    { "t": 1730000002000, "type": "scroll", "data": { "scrollY": 200, "direction": "down" }},

    // User clicks in the input field
    { "t": 1730000005000, "type": "click", "data": { "target": "INPUT", "x": 500, "y": 400 }},

    // User types and submits query (prompt logged automatically by backend)
    { "t": 1730000010000, "type": "prompt", "data": { "text": "What is machine learning?" }},

    // Model responds (logged automatically by backend)
    { "t": 1730000012500, "type": "model_response", "data": {
        "text": "Machine learning is...",
        "model": "gpt-4o-mini",
        "latency_ms": 2500
      }
    },

    // User selects some text from the response
    { "t": 1730000015000, "type": "selection", "data": { "selected_text": "supervised learning" }},

    // User copies the text
    { "t": 1730000016000, "type": "copy", "data": { "selected_text": "supervised learning" }},

    // User scrolls to read more
    { "t": 1730000018000, "type": "scroll", "data": { "scrollY": 600, "direction": "down" }},

    // User asks another question
    { "t": 1730000025000, "type": "prompt", "data": { "text": "Tell me more about neural networks" }},
    { "t": 1730000027800, "type": "model_response", "data": { ... }},

    // User clicks "New Chat" button
    { "t": 1730000030000, "type": "click", "data": { "target": "BUTTON" }},
    // Note: Chat sessionId changes here, but tracking sessionId stays the same!

    // User asks new question in new chat
    { "t": 1730000035000, "type": "prompt", "data": { "text": "What is deep learning?" }},
    { "t": 1730000037200, "type": "model_response", "data": { ... }},

    // User becomes idle (no interaction for 30 seconds)
    { "t": 1730000067000, "type": "activity", "data": { "activity_state": "idle" }},

    // User returns and clicks
    { "t": 1730000090000, "type": "activity", "data": { "activity_state": "active" }},
    { "t": 1730000090100, "type": "click", "data": { ... }}
  ]
}
```

## Current Status: What's Working Now

✅ **Automatic tracking is ACTIVE**:
- Session created on page load
- Scrolls tracked (throttled 500ms)
- Clicks tracked
- Text selection tracked
- Copy events tracked
- Activity/idle state tracked (30s timeout)
- All queries and responses tracked via backend

✅ **Data is being saved to MongoDB**:
- Collection: `sessions`
- Database: `llm_experiment` (or your configured DB)

## How to View Your Tracking Data

### Method 1: Via API
```bash
# Get a specific session
curl http://localhost:8000/session/{trackingSessionId}
```

### Method 2: MongoDB Compass
1. Connect to your MongoDB instance
2. Navigate to `llm_experiment` database
3. Open `sessions` collection
4. View documents - each is a complete user session

### Method 3: Query in MongoDB Shell
```javascript
// Find sessions from a specific user
db.sessions.find({ user_id: "abc-123-def-456" })

// Find sessions using a specific model
db.sessions.find({ model_group: "gpt-4o-mini" })

// Count total events in a session
db.sessions.aggregate([
  { $project: { session_id: 1, event_count: { $size: "$events" } } }
])
```

## Relationship Between Chat Sessions and Tracking Sessions

```
User Visit (1 Tracking Session)
├── Tracking Session ID: user_abc_1730000000000_xyz
│   └── Tracks EVERYTHING during this visit
│
├── Chat Session 1 (sessionId: chat-uuid-1)
│   ├── Query: "What is ML?"
│   ├── Response: "ML is..."
│   └── Query: "Tell me more"
│
├── [User clicks "New Chat"]
│
├── Chat Session 2 (sessionId: chat-uuid-2)
│   ├── Query: "What is DL?"
│   └── Response: "DL is..."
│
└── [User closes tab - tracking session ends]
```

## Important Notes

1. **No code changes needed** - Tracking is already active!
2. **Privacy** - You're tracking behavior, not personal data
3. **Performance** - Events are throttled (scroll) and batched where possible
4. **Storage** - Old sessions can grow large; consider archiving strategy
5. **Two session IDs** - Don't confuse chat `sessionId` with tracking `trackingSessionId`

## Next Steps for Analysis

You can now:
1. Analyze which models get better engagement (scroll depth, time spent)
2. See which queries lead to the most copy/selection (useful responses)
3. Track user drop-off points (when they go idle)
4. Compare chat session lengths across different model groups
5. Build session replay functionality
6. Create conversion funnels

## Testing Your Tracking

To verify tracking is working:

1. Open your app in browser
2. Open Network tab in DevTools
3. Interact with the page (scroll, click, type a query)
4. Watch for POST requests to:
   - `/api/session/start` (on page load)
   - `/api/session/event` (as you interact)
   - `/api/session/end` (when you close the tab)
5. Check MongoDB to see the session data

Your tracking is **LIVE and WORKING** right now! 🎉
