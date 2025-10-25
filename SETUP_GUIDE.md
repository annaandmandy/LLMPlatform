# Complete Setup Guide - LLM Platform

This guide will walk you through setting up the entire ChatGPT simulator platform from scratch.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [MongoDB Setup](#mongodb-setup)
3. [Backend Setup](#backend-setup)
4. [Frontend Setup](#frontend-setup)
5. [Local Testing](#local-testing)
6. [Production Deployment](#production-deployment)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before starting, ensure you have:

### Required
- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **Node.js 18+** and npm - [Download](https://nodejs.org/)
- **Git** - [Download](https://git-scm.com/)

### Accounts Needed
- **MongoDB Atlas** (free tier) - [Sign up](https://www.mongodb.com/cloud/atlas/register)
- **OpenAI API** (or other LLM provider) - [Get API key](https://platform.openai.com/api-keys)
- **Render** (for backend deployment) - [Sign up](https://render.com/)
- **Vercel** (for frontend deployment) - [Sign up](https://vercel.com/)

---

## MongoDB Setup

### Step 1: Create MongoDB Cluster

1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Sign up or log in
3. Click **"Create"** to create a new cluster
4. Choose **FREE** tier (M0 Sandbox)
5. Select a cloud provider and region (choose closest to you)
6. Name your cluster (e.g., "LLMCluster")
7. Click **"Create Cluster"** (takes ~3-5 minutes)

### Step 2: Create Database User

1. Go to **Database Access** in left sidebar
2. Click **"Add New Database User"**
3. Choose **"Password"** authentication
4. Set username: `llmuser`
5. Click **"Autogenerate Secure Password"** (save this!)
6. Set role: **"Read and write to any database"**
7. Click **"Add User"**

### Step 3: Configure Network Access

1. Go to **Network Access** in left sidebar
2. Click **"Add IP Address"**
3. For development: Click **"Allow Access from Anywhere"** (0.0.0.0/0)
   - For production: Add specific IP addresses
4. Click **"Confirm"**

### Step 4: Get Connection String

1. Go to **Database** in left sidebar
2. Click **"Connect"** on your cluster
3. Choose **"Connect your application"**
4. Copy the connection string
5. Replace `<password>` with your database user password
6. Replace `<dbname>` with `llm_experiment`

Example:
```
mongodb+srv://llmuser:YOUR_PASSWORD@cluster0.xxxxx.mongodb.net/llm_experiment?retryWrites=true&w=majority
```

---

## Backend Setup

### Step 1: Navigate to Backend Directory

```bash
cd fastapi-llm-logger
```

### Step 2: Create Virtual Environment (Recommended)

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

```bash
# Copy example file
cp .env.example .env

# Open .env in your editor
nano .env  # or use your preferred editor
```

**Edit .env file:**
```bash
# MongoDB Configuration
MONGODB_URI=mongodb+srv://llmuser:YOUR_PASSWORD@cluster0.xxxxx.mongodb.net/llm_experiment?retryWrites=true&w=majority
MONGO_DB=llm_experiment

# LiteLLM Configuration
LITELLM_MODEL=gpt-4o-mini

# API Keys
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxx
```

### Step 5: Test Backend Locally

```bash
uvicorn main:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

### Step 6: Verify Backend

Open browser or use curl:

```bash
# Check status
curl http://localhost:8000/status

# Expected response:
# {"status":"running","mongodb_connected":true,"model":"gpt-4o-mini"}
```

---

## Frontend Setup

### Step 1: Navigate to Frontend Directory

```bash
cd llm-frontend
```

### Step 2: Install Dependencies

```bash
npm install
```

This will install:
- Next.js 15
- React 18
- TypeScript
- Tailwind CSS
- All required dependencies

### Step 3: Configure Environment Variables

```bash
# Copy example file
cp .env.example .env.local

# Open .env.local in your editor
nano .env.local
```

**Edit .env.local:**
```bash
# For local development
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000

# For production (update after deploying backend)
# NEXT_PUBLIC_BACKEND_URL=https://your-backend.onrender.com
```

### Step 4: Run Development Server

```bash
npm run dev
```

You should see:
```
  ▲ Next.js 15.0.0
  - Local:        http://localhost:3000
  - Ready in 2.3s
```

### Step 5: Test Frontend

1. Open browser to http://localhost:3000
2. You should see "LLM Brand Experiment" page
3. Try entering a query like "What is AI?"
4. Click "Generate Response"
5. You should see a response from the LLM

---

## Local Testing

### Complete Local Test

With both backend (port 8000) and frontend (port 3000) running:

#### 1. Test Query Flow

1. Go to http://localhost:3000
2. Enter query: "Compare Nike and Adidas"
3. Click "Generate Response"
4. Verify response appears

#### 2. Test Event Logging

Open browser console (F12):

```javascript
// Check localStorage for user_id
localStorage.getItem('user_id')

// Check sessionStorage for session_id
sessionStorage.getItem('session_id')
```

#### 3. Test Data Export

```bash
curl http://localhost:8000/export_data > test_data.json
cat test_data.json | jq
```

You should see your queries and events logged.

---

## Production Deployment

### Deploy Backend to Render

#### Step 1: Prepare Repository

```bash
# Initialize git if not already done
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - LLM Platform"

# Create GitHub repo and push
git remote add origin https://github.com/yourusername/llm-platform.git
git push -u origin main
```

#### Step 2: Deploy on Render

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure:
   - **Name**: `llm-backend`
   - **Root Directory**: `fastapi-llm-logger`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 8000`

#### Step 3: Add Environment Variables

In Render dashboard, add:
```
MONGODB_URI=mongodb+srv://...
MONGO_DB=llm_experiment
LITELLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-proj-...
```

#### Step 4: Deploy

1. Click **"Create Web Service"**
2. Wait for deployment (3-5 minutes)
3. Copy your service URL (e.g., `https://llm-backend-xyz.onrender.com`)

#### Step 5: Test Deployed Backend

```bash
curl https://your-backend.onrender.com/status
```

### Deploy Frontend to Vercel

#### Step 1: Prepare for Deployment

```bash
cd llm-frontend

# Build test
npm run build

# Should complete without errors
```

#### Step 2: Deploy to Vercel

**Option A: Vercel CLI**
```bash
npm install -g vercel
vercel
```

**Option B: Vercel Dashboard**
1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click **"Add New"** → **"Project"**
3. Import your GitHub repository
4. Configure:
   - **Framework Preset**: Next.js
   - **Root Directory**: `llm-frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`

#### Step 3: Configure Environment Variables

In Vercel project settings:
```
NEXT_PUBLIC_BACKEND_URL=https://your-backend.onrender.com
```

#### Step 4: Deploy

1. Click **"Deploy"**
2. Wait for deployment (1-2 minutes)
3. Get your deployment URL (e.g., `https://llm-platform.vercel.app`)

#### Step 5: Test Production

1. Visit your Vercel URL
2. Test a query
3. Check that events are logged to backend

---

## Troubleshooting

### Backend Issues

#### MongoDB Connection Error

**Error:** `ServerSelectionTimeoutError`

**Solutions:**
- Verify `MONGODB_URI` is correct
- Check MongoDB IP whitelist (Network Access)
- Ensure database user exists with correct password
- Try connection string tester: `mongosh "your_connection_string"`

#### LiteLLM API Error

**Error:** `AuthenticationError`

**Solutions:**
- Verify `OPENAI_API_KEY` is valid
- Check OpenAI account has credits
- Try different model: `LITELLM_MODEL=gpt-3.5-turbo`

#### Port Already in Use

**Error:** `Address already in use`

**Solutions:**
```bash
# Find process on port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

### Frontend Issues

#### Cannot Connect to Backend

**Error:** Network error or CORS error

**Solutions:**
- Verify backend is running
- Check `NEXT_PUBLIC_BACKEND_URL` in `.env.local`
- Ensure CORS is enabled in backend (already configured in `main.py`)
- Test backend directly: `curl http://localhost:8000/status`

#### Build Errors

**Error:** TypeScript errors

**Solutions:**
```bash
# Clear cache
rm -rf .next node_modules
npm install
npm run build
```

#### User ID Not Set

**Error:** "User session not initialized"

**Solutions:**
- Clear browser localStorage
- Check browser console for errors
- Ensure crypto.randomUUID() is supported (modern browsers)

### General Issues

#### Module Not Found

**Backend:**
```bash
pip install -r requirements.txt --force-reinstall
```

**Frontend:**
```bash
rm -rf node_modules package-lock.json
npm install
```

#### Check Logs

**Render Backend:**
- Go to Render dashboard
- Click on your service
- View **Logs** tab

**Vercel Frontend:**
- Go to Vercel dashboard
- Click on your deployment
- View **Functions** or **Runtime Logs**

---

## Success Checklist

- [ ] MongoDB cluster created and accessible
- [ ] Backend running locally on port 8000
- [ ] Frontend running locally on port 3000
- [ ] Can submit queries and get responses
- [ ] Events are being logged (check via `/export_data`)
- [ ] Backend deployed to Render
- [ ] Frontend deployed to Vercel
- [ ] Production app works end-to-end

---

## Next Steps

1. **Customize Prompts**: Edit LLM system prompt in `main.py`
2. **Add Features**: Implement conversation history
3. **Analytics**: Build dashboard to visualize event data
4. **Scale**: Add caching, rate limiting
5. **Monitor**: Set up logging and monitoring

---

## Support

- **Backend Issues**: See [fastapi-llm-logger/README.md](fastapi-llm-logger/README.md)
- **Frontend Issues**: See [llm-frontend/README.md](llm-frontend/README.md)
- **Architecture**: See [README.md](README.md)

---

**Congratulations!** You now have a fully functional LLM interaction platform with event tracking! 🎉
