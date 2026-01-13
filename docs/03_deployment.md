# Deployment Guide

This document outlines the steps to deploy the LLM Platform to production environments.

## Frontend Deployment (Vercel)

Next.js is optimized for Vercel. Free to deploy website.

1.  **Push code** to a Git repository.
2.  **Import Project** in Vercel.
3.  **Configure Environment Variables**:
    -   `NEXT_PUBLIC_BACKEND_URL`: The public HTTPS URL of your deployed backend.
    -   `NEXT_PUBLIC_CLARITY_ID`: The public Clarity ID of your deployed backend. Used for MS Clarity.
4.  **Deploy**.

## Backend Deployment (Railway)
The backend is deployed on Railway using a Docker container. Railway is recommended because it automatically detects the Dockerfile and handles the build process with zero configuration.
- Plan Note: Railway offers a trial and a generic $5/month Hobby plan which is sufficient for this research platform.
### 1. Initial Setup (First Time Only)
1. Create Account: Log in to Railway.
2. New Project: Click + New Project on the dashboard top-right.
3. Source: Select "Deploy from GitHub repo".
4. Select Repository: Choose the finz-backend (or your project name) repository.
5. ⚠️ CRITICAL STEP: 
    - Configure Root DirectoryRailway will try to find a Dockerfile in the root. Since our backend is in a folder, you must configure this.
    - Click on the repo card Settings (or "Configure" during setup).
    - Find Root Directory settings.
    - Set it to: /backend
    - Reason: This tells Railway to look inside the backend folder for the Dockerfile and requirements.txt.

### 2. Setting Environment Variables (.env)
Railway does not read your local .env file for security reasons. You must manually add these secrets in the dashboard to make the deployment successful.
1. Click on your new Service card in the Railway canvas.
2. Navigate to the Variables tab.
3. Click New Variable (or use "Raw Editor" to paste multiple lines at once).
4. Add the following required keys, and more according to .env.example:
| Variable | Description | Example / Note |
| :--- | :--- | :--- |
| `PORT` | The port the app listens on. | 8000 (Railway often sets this auto, but safe to add) |
| `OPENAI_API_KEY` | Required for the LLM agents to function. | `sk-...` |
| `MONGO_URI` | Connection string for MongoDB Atlas. | `mongodb+srv://...` |
| `LANGCHAIN_TRACING_V2` | Enables LangSmith logging. | `true` |
| `LANGCHAIN_API_KEY` | Your LangSmith secret key. | `lsv2_...` |
| `LANGCHAIN_PROJECT` | The project name in LangSmith. | `finz-research-v1` |

**Note:** Once you save the variables, Railway will automatically trigger a Redeploy.
### 3. Generate Public URLThe backend needs a public address so the Frontend (Vercel) can talk to it.
1. Go to the Settings tab of your service.
2. Scroll down to Networking.
3. Click Generate Domain (or "Custom Domain").
4. Copy this URL (e.g., https://llmplatform-production.up.railway.app).
5. Action Required: Go to your Frontend (Vercel) project settings and update the NEXT_PUBLIC_BACKEND_URL with this new link.