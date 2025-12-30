# LLM Frontend - Next.js Application

## Overview

This is a Next.js frontend application for the LLM Brand Experiment platform. It provides a clean, interactive UI for users to query LLM models and logs all user interactions for analysis.

## Features

- **Query Interface**: Simple, chat-style interface for entering questions
- **Rich Response Rendering**: Markdown support, code highlighting, and structured data display
- **Interactive Product Cards**: Visual display of recommended products with images and prices
- **Shopping Mode**: Specialized UI for guided shopping interviews
- **Event Tracking**: Automatic logging of clicks, scrolls, and browsing behavior
- **Session Management**: Unique user and session ID tracking
- **Responsive Design**: Works seamlessly on desktop and mobile devices

## Tech Stack

- **Next.js 15**: React framework with App Router
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first styling
- **React 18**: Latest React features

## Project Structure

```
llm-frontend/
├── app/
│   ├── page.tsx              # Main home page
│   ├── layout.tsx            # Root layout
│   ├── globals.css           # Global styles
│   └── api/
│       ├── query/route.ts    # Query API route (optional proxy)
│       └── log_event/route.ts # Event logging API route (optional proxy)
├── components/
│   ├── QueryBox.tsx          # Query input component
│   ├── ResponseCard.tsx      # Response display component
│   └── EventTracker.tsx      # Background event tracking
├── lib/
│   └── utils.ts              # Utility functions
├── package.json
├── next.config.js
├── tsconfig.json
├── tailwind.config.ts
└── .env.example
```

## Setup Instructions

### 1. Install Dependencies

```bash
cd llm-frontend
npm install
```

### 2. Configure Environment Variables

Create a `.env.local` file in the root directory:

```bash
cp .env.example .env.local
```

Edit `.env.local`:
```
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

For production, set this to your deployed FastAPI backend URL (e.g., `https://your-backend.onrender.com`).

### 3. Run Development Server

```bash
npm run dev
```

Visit: http://localhost:3000

### 4. Build for Production

```bash
npm run build
npm start
```

## Components

### QueryBox

The main input component that handles:
- User query input via textarea
- Form submission to backend `/query` endpoint
- Loading states and error handling
- Automatic event logging

### ResponseCard

Displays LLM responses with:
- Formatted text output
- Clickable URLs with automatic detection
- Click tracking for all links
- Visual feedback for clicked links

### EventTracker

Background component that tracks:
- Scroll events (with debouncing)
- Page visibility changes
- Navigation events
- All events sent to `/log_event` endpoint

## User Tracking

The application uses two levels of tracking:

1. **User ID**: Persistent across sessions (stored in `localStorage`)
   - Generated on first visit
   - Remains the same for returning users

2. **Session ID**: Unique per browser session (stored in `sessionStorage`)
   - Generated on each new session
   - Resets when browser is closed

## Event Types

The application logs these event types:

- `browse`: Page views and navigation
- `click`: Link clicks within responses
- `scroll`: Scroll position and depth
- `conversion`: Custom conversion actions (extensible)

## API Integration

### Direct Backend Calls

By default, the frontend makes direct calls to the FastAPI backend using `NEXT_PUBLIC_BACKEND_URL`.

### Optional API Routes

The `/app/api/` routes can be used as server-side proxies if needed for:
- Additional security
- Request transformation
- Rate limiting
- Caching

To use them, modify the fetch calls in components to use `/api/query` instead of the direct backend URL.

## Deployment

### Deploy to Vercel

1. Push your code to GitHub
2. Import the project in [Vercel](https://vercel.com)
3. Configure environment variables:
   - `NEXT_PUBLIC_BACKEND_URL`: Your FastAPI backend URL
4. Deploy!

Vercel will automatically:
- Install dependencies
- Build the Next.js application
- Deploy to production
- Provide a custom URL

### Environment Variables in Vercel

Go to your project settings and add:
```
NEXT_PUBLIC_BACKEND_URL=https://your-fastapi-backend.onrender.com
```

## Development Tips

### Testing Locally with Backend

1. Start the FastAPI backend on port 8000
2. Set `NEXT_PUBLIC_BACKEND_URL=http://localhost:8000` in `.env.local`
3. Run `npm run dev`

### Debugging Event Tracking

Open browser console to see event logging:
- All fetch requests are logged
- Errors are displayed in the console

### Customizing Styles

The project uses Tailwind CSS. Modify:
- `tailwind.config.ts` for theme customization
- `app/globals.css` for global styles
- Component classes for specific styling

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Performance

- Next.js automatic code splitting
- Lazy loading of components
- Optimized bundle size
- Server-side rendering support

## Security Considerations

- No API keys exposed in frontend code
- All LLM calls routed through backend
- CORS configured on backend
- Input validation on both client and server

## Future Enhancements

- [x] Markdown & Code Highlighting support
- [x] Product Card display components
- [x] Shopping Mode specialized UI
- [ ] Implement conversation history
- [ ] Add export functionality for user data
- [ ] Support for multiple LLM models
- [ ] Enhanced analytics dashboard
- [ ] A/B testing framework

## License

MIT
