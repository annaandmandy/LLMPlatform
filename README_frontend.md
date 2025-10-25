# 💻 Project Spec: Next.js Frontend for LLM Interaction Experiment (Connects to FastAPI Backend)

## 📘 Overview

You are Claude, a coding assistant that will generate a **Next.js frontend application**.  
This frontend connects to the existing **FastAPI + LiteLLM + MongoDB backend**.

The frontend will:
- Provide a **simple, clean UI** for users to enter queries
- Display generated LLM responses
- Capture and send user **interaction events** (clicks, browsing, conversions)
- Work well for **multiple users**
- Be fully deployable to **Vercel**

---

## 🧩 Architecture

User Browser
↓
Next.js (Frontend on Vercel)
↓ (API calls)
FastAPI Backend (on Render)
↓
MongoDB Atlas


---

## 🎯 Functional Goals

1. Let users input questions or prompts  
2. Send each query to `/query` on the FastAPI backend  
3. Display the model’s response on screen  
4. Log every user event (click, hover, link navigation) through `/log_event`  
5. Handle multiple sessions/users by generating a unique `user_id` per session (store in `localStorage`)  
6. Support configurable backend URL through `.env`  
7. Fully compatible with **Vercel deployment**

---

## 🧱 Project Structure

Claude should generate the following structure:

llm-frontend/
├── app/
│ ├── page.tsx
│ ├── api/
│ │ ├── query/route.ts
│ │ └── log_event/route.ts
├── components/
│ ├── QueryBox.tsx
│ ├── ResponseCard.tsx
│ └── EventTracker.tsx
├── lib/
│ └── utils.ts
├── package.json
├── next.config.js
├── .env.example
└── README.md


---

## ⚙️ Core Functionality

### 1️⃣ Query Input and Display
- A main chat-style page where users can:
  - Type a brand or general query
  - Click “Generate” to send to backend `/query`
  - Display the returned `response` neatly in a card component

### 2️⃣ Event Logging
- All major user actions should trigger a `fetch("/api/log_event", …)` call, which then forwards to backend `/log_event`.
- Event types include:
  - `"click"` — when a user clicks a link or button
  - `"browse"` — when a new page is viewed
  - `"conversion"` — if a simulated “purchase” or action button is pressed
  - `"scroll"` — optional tracking of scroll position or reading depth

### 3️⃣ Session Management
- On first visit, generate a unique UUID and store it in `localStorage` as `user_id`.
- Attach this `user_id` to every request.

### 4️⃣ API Connection
- Environment variable `NEXT_PUBLIC_BACKEND_URL` defines backend base URL.
- All frontend API routes proxy to this backend.

Example:
```ts
const res = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/query`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ user_id, query }),
});

🧩 Components
QueryBox.tsx

Textarea for query input

A toggler to select different models (e.g. gpt 4o-mini).

Submit button

Sends query via POST to backend /query

Displays loading spinner during request

ResponseCard.tsx

Displays LLM response text

Each link in the response triggers a click log:

await fetch("/api/log_event", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    user_id,
    event_type: "click",
    target_url: href,
    query,
  }),
});

EventTracker.tsx

Listens for scroll or navigation events

Periodically logs "browse" or "scroll" activity to backend

📦 Example Files
app/page.tsx
"use client";
import { useState, useEffect } from "react";
import QueryBox from "@/components/QueryBox";
import ResponseCard from "@/components/ResponseCard";
import EventTracker from "@/components/EventTracker";

export default function Home() {
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState("");
  const [userId, setUserId] = useState("");

  useEffect(() => {
    const id = localStorage.getItem("user_id") || crypto.randomUUID();
    localStorage.setItem("user_id", id);
    setUserId(id);
  }, []);

  return (
    <main className="min-h-screen p-8 bg-white">
      <h1 className="text-2xl font-bold mb-4">LLM Brand Experiment</h1>
      <QueryBox query={query} setQuery={setQuery} setResponse={setResponse} userId={userId} />
      {response && <ResponseCard response={response} query={query} userId={userId} />}
      <EventTracker userId={userId} />
    </main>
  );
}

⚙️ .env.example
NEXT_PUBLIC_BACKEND_URL=https://your-fastapi-backend.onrender.com

⚙️ package.json
{
  "name": "llm-frontend",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  },
  "dependencies": {
    "next": "15.0.0",
    "react": "18.2.0",
    "react-dom": "18.2.0",
    "uuid": "^9.0.0"
  }
}

⚙️ next.config.js
const nextConfig = {
  reactStrictMode: true,
  experimental: { serverActions: true },
};
module.exports = nextConfig;

💬 Behavior Summary

All frontend events are POSTed to backend using JSON format.

Frontend never exposes any API keys (backend handles LLM).

Works on both desktop and mobile browsers.

Uses TailwindCSS or basic CSS for layout (Claude can choose).


☁️ Deployment Notes
Local development
npm install
npm run dev


Visit: http://localhost:3000


✅ Output Expectation

Claude must generate:

A complete, runnable Next.js 15 project

All components and pages in working order

.env.example, package.json, and next.config.js

Correct API calls to the backend /query and /log_event endpoints

Clean, readable TypeScript code

✅ Summary

Claude, please generate a complete frontend project that:

Uses Next.js (TypeScript)

Connects to the backend defined in README_backend_claude.md

Records all query, click, and browse events

Is ready to deploy on Vercel

Includes all required files, pages, components, and instructions