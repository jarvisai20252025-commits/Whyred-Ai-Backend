# Whyred AI Backend - FastAPI

FastAPI backend for Whyred AI assistant with async support and automatic documentation.

## Quick Start

```bash
pip install -r requirements.txt
cp .env.example .env
# Fill in your API keys in .env
python start.py
```

## API Endpoints

- `GET /docs` - Interactive API documentation (Swagger UI)
- `POST /api/ask` - Handle text/code/image prompts via Gemini
- `POST /api/ask/test` - Test endpoint (no auth required)
- `POST /api/ask/stream` - Streaming responses
- `POST /api/search` - Google Custom Search + AI response  
- `POST /api/image` - Image analysis
- `GET /api/user/profile` - Get user profile
- `PUT /api/user/profile` - Update user profile
- `GET /api/history` - Get chat history
- `DELETE /api/history` - Clear chat history

## Environment Variables

```
GEMINI_API_KEY=your_gemini_key
GOOGLE_SEARCH_API_KEY=your_google_search_key  
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_PRIVATE_KEY=your_private_key
FIREBASE_CLIENT_EMAIL=your_client_email
PORT=8000
ENVIRONMENT=development
```

## Testing

```bash
python test_api.py
```

## Deploy to Render

1. Push to GitHub
2. Connect repo to Render
3. Set environment variables in Render dashboard
4. Deploy automatically with Python runtime