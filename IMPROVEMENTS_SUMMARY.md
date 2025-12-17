# Product Cards & Chat History Improvements

## ✅ Completed

### 1. Product Cards - Top 1 Only
**Changed**: Product search now returns only the **top 1 result per product** instead of 3

**Files Modified**:
- `agents/product_agent.py`: Changed default `max_results` from 3 to 1
- `agents/graph.py`: Updated product_node to request `max_results: 1`

**Result**: Cleaner, ChatGPT-like product display with one card per recommended product

---

## 🔄 Chat History Persistence (Needs Implementation)

### Problem
- Messages are lost on page refresh
- Session exists but messages don't reload
- Sidebar shows sessions but current chat is empty

### Root Cause
- Messages are only stored in React state (`useState`)
- Backend stores messages in MongoDB
- No mechanism to reload messages from backend on session resume

### Solution Needed

#### Option A: Load from Backend (Recommended)
Add a `loadMessages` function in `useChat.ts`:

```typescript
useEffect(() => {
  const loadSessionMessages = async () => {
    if (!sessionId) return;
    
    try {
      const res = await fetch(`${backendUrl}/session/${sessionId}`);
      const data = await res.json();
      
      // Parse events to reconstruct messages
      const loadedMessages = parseEventsToMessages(data.events);
      setMessages(loadedMessages);
    } catch (err) {
      console.error('Failed to load session messages:', err);
    }
  };
  
  loadSessionMessages();
}, [sessionId]);
```

#### Option B: sessionStorage (Quick Fix)
Persist messages to `sessionStorage` on every update:

```typescript
useEffect(() => {
  if (messages.length > 0) {
    sessionStorage.setItem(`messages_${sessionId}`, JSON.stringify(messages));
  }
}, [messages, sessionId]);

// On init
useEffect(() => {
  const saved = sessionStorage.getItem(`messages_${sessionId}`);
  if (saved) {
    setMessages(JSON.parse(saved));
  }
}, [sessionId]);
```

### Recommended Approach
**Option A** is better because:
- Single source of truth (backend)
- Works across devices/browsers
- Consistent with sidebar data
- No storage limits

### Implementation Steps
1. Add `/session/{session_id}` endpoint to return session with events
2. Add `parseEventsToMessages` utility to convert backend events to Message[]
3. Add `useEffect` in `useChat` to load messages on mount
4. Update sidebar to trigger message reload when session changes

---

## 📝 Next Steps

Would you like me to:
1. **Implement Option A** (backend message loading) - Recommended
2. **Implement Option B** (sessionStorage) - Quick fix
3. **Both** - sessionStorage as fallback, backend as primary

Let me know and I'll implement the solution!
