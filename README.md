# Whyred AI Backend

Node.js + Express backend for Whyred AI assistant.

## Quick Start

```bash
npm install
cp .env.example .env
# Fill in your API keys in .env
npm run dev
```

## API Endpoints

- `POST /api/ask` - Handle text/code/image prompts via Gemini
- `POST /api/search` - Google Custom Search + AI response  
- `POST /api/image` - Image generation/analysis
- `GET /api/user` - Get user data
- `POST /api/user` - Update user data
- `GET /api/history` - Get chat history
- `DELETE /api/history` - Clear chat history

## Environment Variables

```
GEMINI_API_KEY=your_gemini_key
GOOGLE_API_KEY=your_google_search_key  
SEARCH_ENGINE_ID=your_search_engine_id
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_PRIVATE_KEY=your_private_key
FIREBASE_CLIENT_EMAIL=your_client_email
```

## Deploy to Render

1. Push to GitHub
2. Connect repo to Render
3. Set environment variables in Render dashboard
4. Deploy automatically