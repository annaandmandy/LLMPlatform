# Manual Testing Guide

## ✅ Platform Status
- **Backend**: Running on http://localhost:8000
- **Frontend**: Running on http://localhost:3000
- **All async fixes applied**: 11 missing `await` keywords fixed

## Test Steps

### 1. Basic Chat Test
1. Open http://localhost:3000 in your browser
2. Open Developer Console (F12 or Cmd+Option+I)
3. Accept the Terms modal
4. Skip the Experiment ID modal
5. Type a simple message: "Hello"
6. Click Send
7. **Expected**: 
   - ✅ No 404 or 500 errors in console
   - ✅ "Processing:" status appears
   - ✅ Response appears after a few seconds

### 2. Shopping Mode Test
1. Toggle "Shopping Mode" ON (switch in top right of input)
2. Type: "I need wireless headphones under $100"
3. Click Send
4. **Expected**:
   - ✅ Shopping cart icon appears in thinking state
   - ✅ Response with product recommendations
   - ✅ Interactive option buttons appear (if shopping interview)
   - ✅ Beautiful gradient buttons with hover effects

### 3. Streaming Test
1. Send any query
2. Watch the thinking text
3. **Expected**:
   - ✅ Text changes from "Processing: intent_classifier..." 
   - ✅ To "Processing: shopping_agent..." or "Processing: writer_agent..."
   - ✅ Real-time updates as graph executes

### 4. Error Check
Open Console and verify:
- ✅ No "404 Not Found" errors
- ✅ No "500 Internal Server Error" 
- ✅ No "AttributeError: '_asyncio.Future'" errors
- ✅ Event tracking works (POST /session/event returns 200)

## What to Look For

### ✅ Success Indicators
- Messages send and receive successfully
- Streaming status updates appear
- Shopping mode options render as gradient buttons
- No console errors
- Event tracking logs successfully

### ❌ Failure Indicators
- 404 errors on /session/event
- 500 errors on any endpoint
- "AttributeError: '_asyncio.Future'" in backend logs
- Messages don't send
- No streaming updates

## Backend Logs to Monitor

Check the terminal running the backend for:
```
INFO:main:🌊 Streaming query: [your query]
INFO:agents.base_agent:MemoryAgent started execution
INFO:utils.intent_classifier:Intent detected: [intent]
INFO:agents.base_agent:WriterAgent started execution
INFO:     127.0.0.1:xxxxx - "POST /query/stream HTTP/1.1" 200 OK
INFO:     127.0.0.1:xxxxx - "POST /session/event HTTP/1.1" 200 OK
```

## Upgraded Features to Test

1. **Async MongoDB**: All database operations are non-blocking
2. **LangGraph**: Visual agent orchestration with streaming
3. **SSE Streaming**: Real-time progress updates
4. **Shopping UI**: Enhanced gradient buttons with animations
5. **Clean Architecture**: Hooks-based state management

## Known Issues (Pre-existing)
- Experiment ID modal may not close properly (not related to upgrades)
- This is a UI state management issue in page.tsx

---

**If you see any errors, please share the console output and I'll help debug!**
