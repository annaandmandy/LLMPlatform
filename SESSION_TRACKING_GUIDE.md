# Session-Based User Interaction Tracking Guide

This guide explains how to use the new session-based tracking system that has been added to your LLM Platform.

## Overview

The system now tracks detailed user interactions in a **session-centric model** while maintaining backward compatibility with the original `queries` and `events` collections.

### Architecture

**Backend (FastAPI)**
- New `sessions` collection in MongoDB
- Session management endpoints: `/session/start`, `/session/event`, `/session/end`
- Updated `/query` endpoint to log to both legacy collections and sessions

**Frontend (Next.js)**
- `useSession` hook: Manages session lifecycle
- `useEventTracking` hook: Tracks user interactions
- API routes: `/api/session/start`, `/api/session/event`, `/api/session/end`

## Quick Start

### 1. Backend Setup

The backend is already configured with the new session tracking. Start your FastAPI server:

```bash
cd fastapi-llm-logger
python main.py
```

### 2. Frontend Integration

In your main application component, integrate the session tracking hooks:

```tsx
// app/page.tsx or your main component
'use client';

import { useState, useEffect } from 'react';
import { useSession } from '@/lib/useSession';
import { useEventTracking } from '@/lib/useEventTracking';

export default function HomePage() {
  const [userId] = useState(() =>
    localStorage.getItem('userId') || `user_${Date.now()}`
  );
  const [modelGroup] = useState('gpt-4'); // or 'claude-3.5-sonnet', etc.

  // Initialize session tracking
  const sessionId = useSession({
    userId,
    modelGroup,
    experimentId: 'experiment_v1',
  });

  // Initialize event tracking
  const { logEvent } = useEventTracking({
    sessionId,
    trackScroll: true,
    trackClicks: true,
    trackSelection: true,
    trackActivity: true,
  });

  // Save userId to localStorage
  useEffect(() => {
    localStorage.setItem('userId', userId);
  }, [userId]);

  // Example: Log custom events
  const handleFeedback = (feedback: 'up' | 'down') => {
    logEvent('feedback', { feedback });
  };

  return (
    <div>
      <h1>LLM Chat Interface</h1>
      {/* Your chat UI here */}

      <button onClick={() => handleFeedback('up')}>👍</button>
      <button onClick={() => handleFeedback('down')}>👎</button>
    </div>
  );
}
```

## Session Data Structure

Each session in MongoDB follows this structure:

```json
{
  "session_id": "user123_1730000000000_abc123",
  "user_id": "user123",
  "experiment_id": "experiment_v1",
  "model_group": "gpt-4",
  "start_time": "2024-10-27T10:00:00.000Z",
  "end_time": "2024-10-27T10:15:30.000Z",
  "environment": {
    "device": "desktop",
    "browser": "Chrome",
    "os": "macOS",
    "viewport": {
      "width": 1920,
      "height": 1080
    },
    "language": "en-US",
    "connection": "4g"
  },
  "events": [
    {
      "t": 1730000000000,
      "type": "prompt",
      "data": {
        "text": "What is machine learning?"
      }
    },
    {
      "t": 1730000002500,
      "type": "model_response",
      "data": {
        "text": "Machine learning is...",
        "model": "gpt-4",
        "provider": "openai",
        "latency_ms": 2500,
        "response_length": 250,
        "citations": [...]
      }
    },
    {
      "t": 1730000005000,
      "type": "scroll",
      "data": {
        "scrollY": 500,
        "speed": 100,
        "direction": "down"
      }
    },
    {
      "t": 1730000008000,
      "type": "click",
      "data": {
        "target": "BUTTON",
        "x": 150,
        "y": 300
      }
    },
    {
      "t": 1730000010000,
      "type": "feedback",
      "data": {
        "feedback": "up"
      }
    }
  ]
}
```

## Event Types

The system tracks the following event types:

| Event Type | Description | Data Fields |
|------------|-------------|-------------|
| `prompt` | User query to the model | `text` |
| `model_response` | Model's response | `text`, `model`, `provider`, `latency_ms`, `response_length`, `citations` |
| `scroll` | Page scrolling | `scrollY`, `speed`, `direction` |
| `click` | Mouse clicks | `target`, `x`, `y`, `page_url` |
| `hover` | Hovering over elements | `target`, `x`, `y` |
| `selection` | Text selection | `selected_text`, `page_url` |
| `copy` | Text copying | `selected_text`, `page_url` |
| `key` | Keyboard interactions | `target` (key name) |
| `navigate` | Page navigation | `page_url` |
| `activity` | User active/idle state | `activity_state` ("active" or "idle") |
| `feedback` | User feedback on responses | `feedback` ("up", "down", "neutral") |
| `error` | Errors during operation | `error_code`, `text` |

## Custom Event Logging

You can log custom events using the `logEvent` function:

```tsx
const { logEvent } = useEventTracking({ sessionId });

// Example: Log when user opens a citation
const handleCitationClick = (citationUrl: string) => {
  logEvent('navigate', {
    page_url: citationUrl,
    target: 'citation',
  });
};

// Example: Log response viewing time
useEffect(() => {
  const startTime = Date.now();

  return () => {
    const viewTime = Date.now() - startTime;
    logEvent('system', {
      visible_time_ms: viewTime,
      page_url: window.location.pathname,
    });
  };
}, [responseId]);
```

## Configuration Options

### useSession Hook

```tsx
useSession({
  userId: string,           // Required: User identifier
  modelGroup: string,        // Required: Model group/condition
  experimentId?: string,     // Optional: Experiment ID (default: "default")
})
```

### useEventTracking Hook

```tsx
useEventTracking({
  sessionId: string,              // Required: Session ID from useSession
  trackScroll?: boolean,          // Track scrolling (default: true)
  trackClicks?: boolean,          // Track clicks (default: true)
  trackHover?: boolean,           // Track hover events (default: false)
  trackSelection?: boolean,       // Track text selection (default: true)
  trackActivity?: boolean,        // Track active/idle state (default: true)
  scrollThrottle?: number,        // ms between scroll events (default: 500)
  activityIdleTimeout?: number,   // ms before idle (default: 30000)
})
```

## API Endpoints

### Backend (FastAPI)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/session/start` | POST | Start a new session |
| `/session/event` | POST | Add event to session |
| `/session/end` | POST | End a session |
| `/session/{session_id}` | GET | Retrieve session data |
| `/query` | POST | Query LLM (logs to both legacy and sessions) |
| `/log_event` | POST | Legacy event logging |

### Frontend (Next.js API Routes)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/session/start` | POST | Proxy to backend session start |
| `/api/session/event` | POST | Proxy to backend event logging |
| `/api/session/end` | POST | Proxy to backend session end |

## Data Analysis Examples

### Retrieve a session
```bash
curl http://localhost:8000/session/user123_1730000000000_abc123
```

### Query sessions by model group (MongoDB)
```javascript
db.sessions.find({ model_group: "gpt-4" })
```

### Analyze average response latency
```javascript
db.sessions.aggregate([
  { $unwind: "$events" },
  { $match: { "events.type": "model_response" } },
  {
    $group: {
      _id: "$model_group",
      avg_latency: { $avg: "$events.data.latency_ms" }
    }
  }
])
```

### Track user engagement by session duration
```javascript
db.sessions.aggregate([
  {
    $project: {
      model_group: 1,
      duration: {
        $subtract: [
          { $toDate: "$end_time" },
          { $toDate: "$start_time" }
        ]
      }
    }
  },
  {
    $group: {
      _id: "$model_group",
      avg_duration_ms: { $avg: "$duration" }
    }
  }
])
```

## Migration from Legacy System

The new session-based system runs **alongside** the old system:

- `queries` collection: Still receives query logs
- `events` collection: Still receives event logs
- `sessions` collection: NEW - receives all session data

This ensures:
1. **Backward compatibility** - Existing analytics continue to work
2. **Gradual migration** - You can test the new system without breaking existing functionality
3. **Data redundancy** - Critical data is stored in both formats

## Best Practices

1. **Generate unique user IDs**: Use a combination of timestamp and random string
2. **Respect privacy**: Don't track sensitive information in event data
3. **Throttle high-frequency events**: Use the built-in throttling for scroll events
4. **Clean up sessions**: The system automatically ends sessions on page unload
5. **Monitor session size**: Very long sessions may grow large; consider pagination for retrieval

## Troubleshooting

### Session not found error
- Ensure `useSession` is called before `useEventTracking`
- Check that the session was successfully created in the backend

### Events not being logged
- Verify `sessionId` is not empty
- Check network tab for failed API calls
- Ensure backend is running and accessible

### Missing environment data
- Check browser compatibility for navigator properties
- Some connection info may not be available in all browsers

## Next Steps

1. Test the session tracking in your development environment
2. Integrate the hooks into your main application components
3. Customize event tracking based on your specific needs
4. Set up data analysis pipelines using the session data
5. Create visualizations and dashboards for session analytics

For more information, see:
- [README_USERINTERACT_LOG.md](README_USERINTERACT_LOG.md) - Data model specification
- [fastapi-llm-logger/main.py](fastapi-llm-logger/main.py) - Backend implementation
- [llm-frontend/lib/useSession.ts](llm-frontend/lib/useSession.ts) - Session hook
- [llm-frontend/lib/useEventTracking.ts](llm-frontend/lib/useEventTracking.ts) - Event tracking hook
