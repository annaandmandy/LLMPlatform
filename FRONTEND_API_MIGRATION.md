# 🔄 Frontend-Backend API Migration Guide

**Date**: 2025-12-29  
**Status**: Frontend needs updates for new backend structure

---

## 📊 Current Frontend API Calls

### **Identified API Endpoints Used by Frontend**:

| Frontend Call | Current Endpoint | New Backend Endpoint | Status |
|---------------|------------------|----------------------|--------|
| Query (streaming) | `/query/stream` | ✅ `/api/v1/query/stream` | **Needs Update** |
| Query (POST) | `/query` | ✅ `/api/v1/query/` | **Needs Update** |
| Get Session | `/session/{id}` | ✅ `/api/v1/session/{id}` | **Needs Update** |
| Start Session | `/session/start` | ✅ `/api/v1/session/start` | **Needs Update** |
| End Session | `/session/end` | ✅ `/api/v1/session/end` | **Needs Update** |
| Session Event | `/session/event` | ✅ `/api/v1/session/event` | **Needs Update** |
| Get Experiment | `/session/{id}/experiment` | ❌ **NOT IMPLEMENTED** | **Needs Adding** |
| Update Experiment | `/session/{id}/experiment` (POST) | ❌ **NOT IMPLEMENTED** | **Needs Adding** |
| Log Event | `/log_event` | ✅ `/api/v1/session/event` | **Needs Update** |

---

## 🔍 Detailed Analysis

### **1. Query Endpoints** ✅ (Implemented in Backend)

**Frontend Calls**:
- `hooks/useChat.ts:84` - `GET /session/{sessionId}`
- `hooks/useChat.ts:173` - `POST /query/stream`
- `hooks/useChat.ts:251` - `POST /log_event`

**Backend Endpoints** (Already exist):
- ✅ `POST /api/v1/query/` - Standard query
- ✅ `POST /api/v1/query/stream` - Streaming query
- ✅ `GET /api/v1/query/history/{user_id}` - Query history

**Required Changes**:
```typescript
// OLD
const res = await fetch(`${backendUrl}/query/stream`, {...})

// NEW
const res = await fetch(`${backendUrl}/api/v1/query/stream`, {...})
```

---

### **2. Session Endpoints** ✅ (Mostly Implemented)

**Frontend Calls**:
- `lib/useSession.ts:78` - `POST /api/session/start`
- `app/api/session/start/route.ts:12` - `POST /session/start`
- `app/api/session/end/route.ts:12` - `POST /session/end`
- `app/api/session/event/route.ts:29` - `POST /session/event`

**Backend Endpoints** (Already exist):
- ✅ `POST /api/v1/session/start` - Start session
- ✅ `POST /api/v1/session/event` - Add event
- ✅ `POST /api/v1/session/end` - End session
- ✅ `GET /api/v1/session/{session_id}` - Get session

**Required Changes**:
```typescript
// OLD
const response = await fetch(`${backendUrl}/session/start`, {...})

// NEW  
const response = await fetch(`${backendUrl}/api/v1/session/start`, {...})
```

---

### **3. Event Logging** ⚠️ (Needs Consolidation)

**Frontend Calls**:
- `hooks/useChat.ts:251` - `POST /log_event`
- `components/EventTracker.tsx:37` - `POST /log_event`
- `components/MessageHistory.tsx:92` - `POST /log_event`
- `app/api/log_event/route.ts:12` - `POST /log_event`

**Backend Implementation**:
- ✅ `POST /api/v1/session/event` - Add session event

**Recommendation**: Replace `/log_event` with `/api/v1/session/event`

**Required Changes**:
```typescript
// OLD
await fetch(`${backendUrl}/log_event`, {
  method: 'POST',
  body: JSON.stringify({
    user_id, session_id, event_type, ...
  })
})

// NEW
await fetch(`${backendUrl}/api/v1/session/event`, {
  method: 'POST',
  body: JSON.stringify({
    session_id,
    event_type,  
    event_data: {...}
  })
})
```

---

### **4. Experiment Endpoints** ❌ (MISSING IN BACKEND!)

**Frontend Calls**:
- `app/page.tsx:128` - `GET /session/{sessionId}/experiment`
- `app/page.tsx:195` - `POST /session/{sessionId}/experiment`

**Backend Status**: **NOT IMPLEMENTED**

**Need to Add**:
```python
# backend/app/api/v1/sessions.py

@router.get("/{session_id}/experiment")
async def get_session_experiment(
    session_id: str,
    db = Depends(get_db)
):
    """Get experiment data for session."""
    session = await db["sessions"].find_one({"session_id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "experiment_id": session.get("experiment_id"),
        "model_group": session.get("model_group"),
        # ... other experiment data
    }

@router.post("/{session_id}/experiment")
async def update_session_experiment(
    session_id: str,
    experiment_data: dict,
    db = Depends(get_db)
):
    """Update experiment data for session."""
    result = await db["sessions"].update_one(
        {"session_id": session_id},
        {"$set": {
            "experiment_id": experiment_data.get("experiment_id"),
            "model_group": experiment_data.get("model_group"),
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"success": True}
```

---

## 🛠️ Implementation Checklist

### **Backend Changes Needed** ❌

1. **Add Experiment Endpoints** to `app/api/v1/sessions.py`:
   ```python
   @router.get("/{session_id}/experiment")
   @router.post("/{session_id}/experiment")
   ```

### **Frontend Changes Needed** ✅

#### **1. Update Base URL in All Files** (12 files)

**Files to Update**:
- `hooks/useChat.ts`
- `lib/useSession.ts`
- `lib/useEventTracking.ts`
- `app/api/session/start/route.ts`
- `app/api/session/end/route.ts`
- `app/api/session/event/route.ts`
- `app/api/query/route.ts`
- `app/api/log_event/route.ts`
- `app/page.tsx`
- `components/EventTracker.tsx`
- `components/MessageHistory.tsx`
- `components/QueryBox.tsx`

**Change Pattern**:
```typescript
// BEFORE
`${backendUrl}/session/start`
`${backendUrl}/query/stream`
`${backendUrl}/log_event`

// AFTER
`${backendUrl}/api/v1/session/start`
`${backendUrl}/api/v1/query/stream`
`${backendUrl}/api/v1/session/event`  // Replace log_event
```

#### **2. Update Event Logging**

Change from `/log_event` → `/api/v1/session/event`:

```typescript
// OLD payload
{
  user_id: string,
  session_id: string,
  event_type: string,
  query?: string,
  page_url?: string,
}

// NEW payload (matches SessionEventRequest schema)
{
  session_id: string,
  event_type: string,
  event_data: {
    query?: string,
    page_url?: string,
    // ... other data
  }
}
```

#### **3. Update Experiment Calls**

Once backend endpoints are added:
```typescript
// GET experiment
const res = await fetch(`${backendUrl}/api/v1/session/${sessionId}/experiment`)

// POST experiment
await fetch(`${backendUrl}/api/v1/session/${sessionId}/experiment`, {
  method: 'POST',
  body: JSON.stringify({
    experiment_id: experimentId,
    model_group: modelGroup,
  })
})
```

---

## 📝 Migration Steps

### **Step 1: Backend - Add Missing Endpoints**

1. Open `backend/app/api/v1/sessions.py`
2. Add experiment endpoints (see code above)
3. Test with curl/Insomnia

### **Step 2: Frontend - Create Migration Script**

Create `frontend/scripts/migrate-api-urls.sh`:

```bash
#!/bin/bash

# Migrate API URLs to new v1 structure

files=(
  "hooks/useChat.ts"
  "lib/useSession.ts"
  "lib/useEventTracking.ts"
  "app/api/session/start/route.ts"
  "app/api/session/end/route.ts"
  "app/api/session/event/route.ts"
  "app/api/query/route.ts"
  "app/api/log_event/route.ts"
  "app/page.tsx"
  "components/EventTracker.tsx"
  "components/MessageHistory.tsx"
  "components/QueryBox.tsx"
)

for file in "${files[@]}"; do
  echo "Updating $file..."
  
  # Update session endpoints
  sed -i '' 's|/session/start|/api/v1/session/start|g' "$file"
  sed -i '' 's|/session/end|/api/v1/session/end|g' "$file"
  sed -i '' 's|/session/event|/api/v1/session/event|g' "$file"
  sed -i '' 's|/session/\${|/api/v1/session/${|g' "$file"
  
  # Update query endpoints  
  sed -i '' 's|/query/stream|/api/v1/query/stream|g' "$file"
  sed -i '' 's|/query\`|/api/v1/query/|g' "$file"
  
  # Update log_event -> session/event
  sed -i '' 's|/log_event|/api/v1/session/event|g' "$file"
done

echo "✅ Migration complete!"
```

### **Step 3: Manual Updates**

Some complex calls need manual updates:

1. **useChat.ts** - Update session loading:
   ```typescript
   // Line 84
   const res = await fetch(`${backendUrl}/api/v1/session/${sessionId}`)
   ```

2. **useChat.ts** - Update streaming query:
   ```typescript
   // Line 173
   const res = await fetch(`${backendUrl}/api/v1/query/stream`, {...})
   ```

3. **page.tsx** - Update experiment calls:
   ```typescript
   // Line 128
   const res = await fetch(`${backendUrl}/api/v1/session/${sessionId}/experiment`)
   
   // Line 195
   await fetch(`${backendUrl}/api/v1/session/${sessionId}/experiment`, {...})
   ```

### **Step 4: Test**

1. Start backend: `uvicorn app.main:app --reload`
2. Start frontend: `npm run dev`
3. Test each feature:
   - ✅ Send query
   - ✅ Streaming response
   - ✅ Session creation  
   - ✅ Event logging
   - ✅ Experiment tracking

---

## 🎯 Summary

### **Backend TODO**:
1. ❌ Add `/api/v1/session/{id}/experiment` (GET)
2. ❌ Add `/api/v1/session/{id}/experiment` (POST)

### **Frontend TODO**:
1. ✅ Update 12 files with new API paths
2. ✅ Replace `/log_event` with `/api/v1/session/event`
3. ✅ Update event payload structure
4. ✅ Test all endpoints

### **Estimated Effort**:
- Backend: 30 minutes (2 endpoints)
- Frontend: 1 hour (12 files + testing)
- **Total: 1.5 hours**

---

**Status**: Ready to migrate once backend experiment endpoints are added!
