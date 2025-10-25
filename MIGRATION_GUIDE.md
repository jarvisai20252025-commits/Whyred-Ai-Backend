# Migration Guide: Node.js to FastAPI

## Overview
Successfully migrated from Node.js/Express to FastAPI + Uvicorn for better performance and AI integration.

## Key Changes

### Backend Architecture
- **Before**: Node.js + Express
- **After**: Python + FastAPI + Uvicorn
- **Benefits**: Better async support, automatic API docs, type safety

### File Structure
```
backend/
├── main.py              # FastAPI app (was src/server.js)
├── start.py             # Startup script
├── requirements.txt     # Python deps (was package.json)
├── routers/            # API routes (was src/routes/)
│   ├── ask.py
│   ├── search.py
│   ├── user.py
│   ├── history.py
│   └── image.py
├── services/           # Business logic (was src/services/)
│   ├── gemini_service.py
│   ├── firebase_service.py
│   └── search_service.py
└── middleware/         # Auth middleware (was src/middleware/)
    └── auth.py
```

### API Endpoints (Unchanged)
All endpoints remain the same for frontend compatibility:
- `POST /api/ask`
- `POST /api/search`
- `POST /api/image`
- `GET /api/history`
- etc.

### New Features
- **Interactive Docs**: Visit `/docs` for Swagger UI
- **Streaming**: Enhanced streaming responses
- **Type Safety**: Pydantic models for request/response validation
- **Better Error Handling**: More detailed error responses

## Running the New Backend

### Development
```bash
pip install -r requirements.txt
python start.py
```

### Production
```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Frontend Changes
- Updated `baseUrl` in Flutter `api_service.dart`
- All API calls remain compatible
- No changes needed to request/response formats

## Deployment
- Updated `render.yaml` for Python runtime
- Added `runtime.txt` for Python version
- Same environment variables as before

## Testing
```bash
python test_api.py
```

## Migration Complete
All Node.js files have been removed. The backend now runs entirely on FastAPI + Python.