# Getting Started

This guide covers how to set up the **LLM Platform** locally, including both the FastAPI backend and the Next.js frontend.

## Prerequisites

Ensure you have the following installed:

- **Python 3.11+**: [Download Python](https://www.python.org/downloads/)
- **Node.js 18+ & npm**: [Download Node.js](https://nodejs.org/)
- **Docker & Docker Compose** (Optional, for containerized run): [Get Docker](https://www.docker.com/)
- **MongoDB Atlas Account**: Required for Vector Search features. [Sign up](https://www.mongodb.com/atlas)
- **API Keys**: At least one LLM provider key (OpenAI, Anthropic, Google, or OpenRouter).

---

## 1. Clone the Repository

```bash
git clone https://github.com/annaandmandy/LLMPlatform.git
cd LLMPlatform
```

## 2. Backend Setup

The backend is built with FastAPI and handles all LLM orchestration.

### Local Python Environment

1.  **Navigate to backend:**
    ```bash
    cd backend
    ```

2.  **Create virtual environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # macOS/Linux
    # .venv\Scripts\activate   # Windows
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment:**
    Copy the example environment file:
    ```bash
    cp .env.example .env
    ```
    Edit `.env` and populate your keys:
    - `MONGODB_URI`: Your Atlas connection string.
    - `OPENAI_API_KEY` (or others): Your LLM provider key.

5.  **Run the Server:**
    ```bash
    uvicorn app.main:app --reload --reload-dir app
    ```
    The backend will be available at [http://localhost:8000](http://localhost:8000).

### Docker(For Railway Deployment)
The Dockerfile and docker-compose.yml for Railway is already written and works while testing, no need to adjust.


## 3. Frontend Setup

The frontend is a Next.js application.

1.  **Navigate to frontend:**
    ```bash
    cd frontend
    ```

2.  **Install Dependencies:**
    ```bash
    npm install
    ```

3.  **Configure Environment:**
    ```bash
    cp .env.example .env.local
    ```
    Ensure `NEXT_PUBLIC_BACKEND_URL` is set to `http://localhost:8000`.

4.  **Run the Development Server:**
    ```bash
    npm run dev
    ```
    The frontend will be available at [http://localhost:3000](http://localhost:3000).

## 4. Verification

1.  Open [http://localhost:3000](http://localhost:3000) in your browser.
2.  Enter a query (e.g., "Whats the weather like today?").
3.  Check the backend logs to see the request being processed by the agents.
4.  Visit [http://localhost:8000/docs](http://localhost:8000/docs) to explore the API directly.

## 5. Development Workflow

-   **Backend Changes**: The server auto-reloads when you modify files in `backend/app`.
-   **Frontend Changes**: Next.js Fast Refresh will update the UI immediately.
