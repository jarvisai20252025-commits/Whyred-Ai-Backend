from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
from dotenv import load_dotenv
from datetime import datetime
import json

from routers import ask, search, user, history, image
from middleware.auth import get_current_user
from services.firebase_service import init_firebase

load_dotenv()

# Initialize Firebase
init_firebase()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Whyred AI Backend API",
    version="1.0.0",
    description="FastAPI backend for Whyred AI assistant"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ask.router, prefix="/api/ask", tags=["ask"])
app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(user.router, prefix="/api/user", tags=["user"])
app.include_router(history.router, prefix="/api/history", tags=["history"])
app.include_router(image.router, prefix="/api/image", tags=["image"])

@app.get("/")
async def root():
    return {
        "message": "Whyred AI Backend API",
        "version": "1.0.0",
        "endpoints": ["/api/ask", "/api/search", "/api/image", "/api/user", "/api/history"]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "OK",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))