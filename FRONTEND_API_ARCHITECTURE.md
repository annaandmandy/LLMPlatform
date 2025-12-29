# 🏗️ Frontend API Architecture - Recommendation

**Date**: 2025-12-29  
**Status**: ✅ **Centralized API Client Created**

---

## 🤔 The Question

Should all frontend API calls be organized in the `frontend/app/api` folder?

---

## 📊 Current State Analysis

### **What You Have Now** (Mixed):

1. **Next.js API Routes** (`app/api/`):
   - `app/api/query/route.ts` - Proxy to backend
   - `app/api/session/start/route.ts` - Proxy to backend
   - `app/api/session/end/route.ts` - Proxy to backend
   - `app/api/session/event/route.ts` - Proxy to backend

2. **Direct Backend Calls**:
   - `hooks/useChat.ts` → Direct fetch to backend
   - `lib/useEventTracking.ts` → Direct fetch to backend
   - `components/*.tsx` → Direct fetch to backend
   - `app/page.tsx` → Direct fetch to backend

### **The Problem**:
- ❌ Inconsistent (some proxy, some direct)
- ❌ Code duplication (fetch logic repeated)
- ❌ Hard to maintain
- ❌ Next.js API routes add unnecessary latency

---

## ✅ Recommended Architecture

### **Use Centralized API Client (Created: `lib/apiClient.ts`)**

**Why This is Better**:
1. ✅ **Single Source of Truth** - All API logic in one place
2. ✅ **Type Safety** - TypeScript interfaces for all requests/responses
3. ✅ **Consistent Error Handling** - Standardized error messages
4. ✅ **Easy to Test** - Mock API client in tests
5. ✅ **No Extra Latency** - Direct backend calls
6. ✅ **Easy to Refactor** - Change one file vs many

---

## 📁 Recommended Structure

```
frontend/
├── lib/
│   ├── apiClient.ts          ✅ NEW - All backend API calls
│   ├── useSession.ts          → Uses apiClient
│   └── useEventTracking.ts    → Uses apiClient
│
├── hooks/
│   └── useChat.ts             → Uses apiClient
│
├── components/
│   ├── MessageHistory.tsx     → Uses apiClient.logEvent()
│   ├── EventTracker.tsx       → Uses apiClient.logEvent()
│   └── QueryBox.tsx           → Uses apiClient.logEvent()
│
└── app/
    ├── api/                   ❌ REMOVE (not needed as proxies)
    │   ├── query/            
    │   └── session/          
    └── page.tsx               → Uses apiClient
```

---

## 🔑 When to Use Next.js API Routes vs Direct Calls

### **Use Next.js API Routes When**:
1. ❗ **Hiding API keys** - Keep secrets server-side
2. ❗ **Server-side processing** - Transform data before sending to client
3. ❗ **Authentication** - Verify user tokens server-side
4. ❗ **Rate limiting** - Control client access server-side

### **Use Direct Calls (via apiClient.ts) When**:
1. ✅ **Backend handles auth** - Your FastAPI backend does this
2. ✅ **No secrets exposed** - Backend URL is public anyway
3. ✅ **Client-side only** - React components making calls
4. ✅ **Simple pass-through** - No transformation needed

**Your Case**: You have a separate FastAPI backend that handles ALL logic and auth.  
**Answer**: Use direct calls via `apiClient.ts` ✅

---

## 🎯 Migration Plan

### **Step 1: Remove Next.js API Route Proxies** ✅

These are just adding latency:
```bash
rm -rf frontend/app/api/query
rm -rf frontend/app/api/session
```

### **Step 2: Update Code to Use apiClient**

**Before** (Scattered):
```typescript
// In useChat.ts
const res = await fetch(`${backendUrl}/api/v1/query/stream`, {...})

// In MessageHistory.tsx
await fetch(`${backendUrl}/api/v1/session/event`, {...})
```

**After** (Centralized):
```typescript
// In useChat.ts
import { streamQuery } from '@/lib/apiClient';
const stream = await streamQuery(request);

// In MessageHistory.tsx
import { logEvent } from '@/lib/apiClient';
logEvent(sessionId, 'click', { target_url: href });
```

### **Step 3: Update All Files** (Examples)

#### **hooks/useChat.ts**:
```typescript
import { streamQuery, getSession, logEvent } from '@/lib/apiClient';

// Replace fetch calls with:
const stream = await streamQuery({...});
const session = await getSession(sessionId);
logEvent(sessionId, 'browse', { query, page_url });
```

#### **components/MessageHistory.tsx**:
```typescript
import { logEvent } from '@/lib/apiClient';

const handleLinkClick = async (href: string, query: string) => {
  logEvent(sessionId, 'click', {
    target_url: href,
    page_url: window.location.href,
    text: query,
  });
  setClickedLinks(new Set([...clickedLinks, href]));
};
```

---

## 📊 Comparison

| Approach | Latency | Maintainability | Type Safety | Complexity |
|----------|---------|-----------------|-------------|------------|
| **Next.js API Routes** | High (2 hops) | Low | Medium | High |
| **Direct Fetch** | Low (1 hop) | Low | Low | Medium |
| **✅ apiClient.ts** | Low (1 hop) | High | High | Low |

---

## 🚀 Benefits of apiClient.ts

### **1. Single Source of Truth**
```typescript
// Change backend URL once, affects all calls
const getBackendUrl = () => process.env.NEXT_PUBLIC_BACKEND_URL;
```

### **2. Type Safety**
```typescript
// TypeScript knows request/response structure
const result: QueryResponse = await sendQuery(request);
```

### **3. Error Handling**
```typescript
// Standardized error messages
throw new Error(`Query failed: ${response.status}`);
```

### **4. Easy Testing**
```typescript
// Mock entire API client
jest.mock('@/lib/apiClient');
```

### **5. Developer Experience**
```typescript
// Autocomplete, type checking, inline docs
logEvent(sessionId, 'click', { /* IntelliSense here! */ });
```

---

## 🎯 Answer to Your Question

**Question**: "Should frontend API be organized in `app/api` folder?"

**Answer**: **No, use centralized API client instead** (`lib/apiClient.ts`)

**Why**:
1. Your `app/api` routes are just dumb proxies
2. They add latency without adding value
3. Your FastAPI backend already handles auth/logic
4. Centralized client is more maintainable

**Exception**: Keep `app/api` routes ONLY if they:
- Transform/process data server-side
- Hide API keys
- Implement server-side logic

---

## 📋 Action Items

### **Option 1: Clean Architecture** (Recommended)
1. ✅ Use `lib/apiClient.ts` (already created)
2. ❌ Delete `app/api/*` proxies
3. ✅ Update all components/hooks to use apiClient
4. ✅ Enjoy better performance and maintainability

### **Option 2: Keep Proxies** (Not Recommended)
1. Keep `app/api/*` routes
2. Update all code to use `/api/*` instead of direct calls
3. Accept added latency
4. Harder to maintain

---

## 🎉 Summary

**Best Practice for Your Architecture**:
```
Frontend (Next.js) 
    ↓ (direct call via apiClient.ts)
Backend (FastAPI) 
    ↓
Database (MongoDB)
```

**Not**:
```
Frontend (Next.js) 
    ↓
Next.js API Routes (unnecessary proxy)
    ↓
Backend (FastAPI)
    ↓
Database (MongoDB)
```

---

**Recommendation**: ✅ **Use `lib/apiClient.ts` and remove `app/api` proxies**

This gives you:
- Better performance (no extra hop)
- Better maintainability (single source)
- Better type safety (TypeScript)
- Cleaner architecture

---

**Next Steps**:
1. Review `lib/apiClient.ts`
2. Decide: Migrate or keep current?
3. If migrate: Update components gradually
4. If keep: Document why proxies are needed

Would you like me to help migrate the code to use apiClient.ts?
