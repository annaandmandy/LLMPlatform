# LLM Platform - ChatGPT Simulator with Event Tracking

A full-stack application for LLM interaction experiments with comprehensive user event tracking and analytics.

## Project Overview

This platform consists of two main components:
1. **FastAPI Backend** - Handles LLM queries via LiteLLM and stores all interactions in MongoDB
2. **Next.js Frontend** - Provides an interactive UI for users to query LLMs and automatically tracks user behavior

### Architecture

```
User Browser
    ↓
Next.js Frontend (Vercel)
    ↓ HTTP/JSON
FastAPI Backend (Render)
    ↓
MongoDB Atlas (Cloud Database)
```

## Features

### Backend Features
- Multi-model LLM support via LiteLLM
- MongoDB storage for queries and events
- RESTful API endpoints for queries and event logging
- Data export functionality for analysis
- Multi-user support with session tracking
- Docker deployment ready

### Frontend Features
- Clean, responsive chat-style interface
- Real-time LLM response display
- Automatic event tracking (clicks, scrolls, browsing)
- Unique user and session ID management
- Link click tracking with visual feedback
- Vercel deployment ready

## Project Structure

```
LLMPlatform/
├── fastapi-llm-logger/          # Backend application
│   ├── main.py                  # FastAPI app with all endpoints
│   ├── requirements.txt         # Python dependencies
│   ├── Dockerfile              # Docker configuration
│   ├── .env.example            # Environment variables template
│   ├── .gitignore
│   └── README.md
│
├── llm-frontend/                # Frontend application
│   ├── app/
│   │   ├── page.tsx            # Main page
│   │   ├── layout.tsx          # Root layout
│   │   ├── globals.css         # Global styles
│   │   └── api/
│   │       ├── query/route.ts
│   │       └── log_event/route.ts
│   ├── components/
│   │   ├── QueryBox.tsx        # Query input component
│   │   ├── ResponseCard.tsx    # Response display
│   │   └── EventTracker.tsx    # Event tracking
│   ├── lib/
│   │   └── utils.ts            # Utility functions
│   ├── package.json
│   ├── next.config.js
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── .env.example
│   ├── .gitignore
│   └── README.md
│
├── README_backend.md            # Backend specification
├── README_frontend.md           # Frontend specification
└── README.md                    # This file
```

## Quick Start

### Prerequisites

- **Backend**: Python 3.11+, MongoDB Atlas account
- **Frontend**: Node.js 18+, npm
- **APIs**: OpenAI API key (or other LLM provider)

### Backend Setup

```bash
# Navigate to backend directory
cd fastapi-llm-logger

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your MongoDB URI and API keys

# Run the server
uvicorn main:app --reload
```

Backend runs at: http://localhost:8000

### Frontend Setup

```bash
# Navigate to frontend directory
cd llm-frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local
# Edit .env.local with backend URL

# Run development server
npm run dev
```

Frontend runs at: http://localhost:3000

## API Endpoints

### Backend API

#### `POST /query`
Generate an LLM response and log the query.

**Request:**
```json
{
  "user_id": "u_123",
  "session_id": "s_456",
  "query": "What are the best chocolate brands?"
}
```

**Response:**
```json
{
  "response": "Based on quality and taste...",
  "source": [{"title": "...", "url": "...", "content": "..."}]
}
```

#### `POST /log_event`
Record user interaction events.

**Request:**
```json
{
  "user_id": "u_123",
  "session_id": "s_456",
  "event_type": "click",
  "query": "chocolate brands",
  "target_url": "https://example.com",
  "page_url": "https://yourapp.com",
  "extra_data": {"scroll_depth": 0.75}
}
```

#### `GET /export_data`
Export all logged data for analysis.

**Response:**
```json
{
  "total_records": 150,
  "queries_count": 50,
  "events_count": 100,
  "data": [...]
}
```

#### `GET /status`
Health check endpoint.

## Event Tracking

The platform tracks the following user events:

| Event Type | Description | Triggered When |
|------------|-------------|----------------|
| `browse` | Page views | User views results |
| `click` | Link clicks | User clicks any URL in response |
| `scroll` | Scrolling behavior | User scrolls page (debounced) |
| `conversion` | Custom actions | User performs target action |

## Environment Configuration

### Backend (.env)

```bash
MONGODB_URI=mongodb+srv
MONGO_DB=llm_experimentß
OPENAI_API_KEY=sk-xxxxx
```

### Frontend (.env.local)

```bash
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
# or production: https://your-backend.onrender.com
```

## Deployment

### Deploy Backend to Render

1. Push code to GitHub
2. Create new **Web Service** on [Render](https://render.com)
3. Connect your repository
4. Select `fastapi-llm-logger` directory
5. Set build command: `pip install -r requirements.txt`
6. Set start command: `uvicorn main:app --host 0.0.0.0 --port 8000`
7. Add environment variables from `.env.example`
8. Deploy!

### Deploy Frontend to Vercel

1. Push code to GitHub
2. Import project on [Vercel](https://vercel.com)
3. Select `llm-frontend` as root directory
4. Add environment variable:
   - `NEXT_PUBLIC_BACKEND_URL`: Your Render backend URL
5. Deploy!

### Deploy Backend with Docker

```bash
cd fastapi-llm-logger
docker build -t llm-logger .
docker run -p 8000:8000 --env-file .env llm-logger
```

## MongoDB Setup

1. Create free cluster on [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create database user with read/write permissions
3. Whitelist IP addresses (0.0.0.0/0 for development)
4. Get connection string
5. Add to backend `.env` file

### Collections

The application uses two collections:

**`queries`**
- user_id
- session_id
- query
- response
- model_used
- timestamp
- sources

**`events`**
- user_id
- session_id
- event_type
- query
- target_url
- page_url
- extra_data
- timestamp

## Data Analysis

Export all data via the `/export_data` endpoint:

```bash
curl http://localhost:8000/export_data > data.json
```

Use the exported JSON for:
- User behavior analysis
- Click-through rate calculation
- Query pattern analysis
- A/B testing results
- Conversion tracking

## Development Workflow

### Local Development

1. Start MongoDB (or use Atlas)
2. Start backend: `cd fastapi-llm-logger && uvicorn main:app --reload`
3. Start frontend: `cd llm-frontend && npm run dev`
4. Open http://localhost:3000

### Testing

**Backend:**
```bash
# Test status endpoint
curl http://localhost:8000/status

# Test query endpoint
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "session_id": "test", "query": "Hello"}'
```

**Frontend:**
- Open browser console
- Submit a query
- Check network tab for API calls
- Verify events are logged

## Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **LiteLLM**: Unified LLM API interface
- **MongoDB**: NoSQL database for event storage
- **PyMongo**: MongoDB driver for Python
- **Uvicorn**: ASGI server

### Frontend
- **Next.js 15**: React framework with App Router
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first styling
- **React 18**: Latest React features

## Security Considerations

- API keys stored in environment variables
- CORS configured for frontend access
- No sensitive data in frontend code
- MongoDB connection with authentication
- Input validation on all endpoints
- Rate limiting recommended for production

## Performance Optimizations

- Next.js automatic code splitting
- Debounced scroll event tracking
- Efficient MongoDB indexing
- Connection pooling
- Lazy loading of components

## Troubleshooting

### Backend Issues

**MongoDB Connection Failed**
- Check `MONGODB_URI` in `.env`
- Verify IP whitelist in MongoDB Atlas
- Check database user permissions

**LLM API Errors**
- Verify API key in `.env`
- Check API quota/billing
- Ensure model name is correct

### Frontend Issues

**Cannot Connect to Backend**
- Verify `NEXT_PUBLIC_BACKEND_URL` is set
- Check backend is running
- Check CORS configuration

**Events Not Logging**
- Check browser console for errors
- Verify user/session IDs are set
- Check network tab for failed requests

## Future Enhancements

- [ ] Real-time response streaming
- [ ] Conversation history
- [ ] Multiple LLM model selection
- [ ] Analytics dashboard
- [ ] User authentication
- [ ] Rate limiting
- [ ] Caching layer
- [ ] WebSocket support
- [ ] Advanced filtering in export
- [ ] Automated testing suite

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - See LICENSE file for details

## Support

For issues and questions:
- Check the individual README files in each directory
- Review the specification files (README_backend.md, README_frontend.md)
- Open an issue on GitHub

## Authors

Generated with Claude Code based on comprehensive specifications for LLM interaction logging and analysis.

---

**Happy Experimenting!** 🚀
