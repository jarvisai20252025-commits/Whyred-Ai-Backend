from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import json
import asyncio
from datetime import datetime
import logging

from middleware.auth import get_current_user, get_optional_user
from services.gemini_service import gemini_service
from services.firebase_service import get_firestore_client
from slowapi import Limiter
from slowapi.util import get_remote_address

logger = logging.getLogger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

class AskRequest(BaseModel):
    prompt: str
    type: str = "text"
    imageData: Optional[str] = None

class TestRequest(BaseModel):
    prompt: str = "Hello, this is a test message."

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        is_healthy = await gemini_service.health_check()
        model_info = gemini_service.get_model_info()
        
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            **model_info
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@router.post("/test")
async def test_endpoint(request: TestRequest):
    """Test endpoint without authentication"""
    try:
        logger.info(f"Test endpoint called with prompt: {request.prompt}")
        
        response = await gemini_service.generate_text(request.prompt)
        
        return {
            "response": response,
            "timestamp": datetime.now().isoformat(),
            "model": "test-mode",
            "success": True
        }
    except Exception as e:
        logger.error(f"Test endpoint error: {e}")
        return {
            "response": f"Test response for: \"{request.prompt}\". The AI service is currently being optimized.",
            "timestamp": datetime.now().isoformat(),
            "model": "fallback",
            "success": False,
            "error": str(e)
        }

@router.post("/")
@limiter.limit("100/15minutes")
async def ask_endpoint(request_data: Request, ask_request: AskRequest, user=Depends(get_current_user)):
    """Main ask endpoint with authentication"""
    try:
        if not ask_request.prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")

        logger.info(f"Processing {ask_request.type} request for user: {user['uid']}")
        logger.info(f"Prompt: {ask_request.prompt[:100]}...")

        processing_start = datetime.now()
        
        # Generate response based on type
        if ask_request.type == "image":
            if not ask_request.imageData:
                raise HTTPException(status_code=400, detail="Image data required for image analysis")
            response = await gemini_service.generate_from_image(ask_request.prompt, ask_request.imageData)
        elif ask_request.type == "code":
            response = await gemini_service.generate_code(ask_request.prompt)
        elif ask_request.type == "search":
            response = await gemini_service.generate_search(ask_request.prompt)
        else:
            response = await gemini_service.generate_text(ask_request.prompt)

        processing_time = (datetime.now() - processing_start).total_seconds() * 1000
        logger.info(f"Response generated in {processing_time:.0f}ms")

        # Save to history
        try:
            db = get_firestore_client()
            await asyncio.to_thread(
                db.collection('chat_history').add,
                {
                    'userId': user['uid'],
                    'prompt': ask_request.prompt,
                    'response': response,
                    'type': ask_request.type,
                    'timestamp': datetime.now(),
                    'processingTime': processing_time,
                    'model': 'gemini-2.0-flash-exp',
                    'success': True
                }
            )
        except Exception as db_error:
            logger.error(f"Failed to save to history: {db_error}")

        return {
            "response": response,
            "timestamp": datetime.now().isoformat(),
            "processingTime": processing_time,
            "type": ask_request.type,
            "success": True
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ask endpoint error: {e}")
        
        # Try to save error to history
        try:
            db = get_firestore_client()
            await asyncio.to_thread(
                db.collection('chat_history').add,
                {
                    'userId': user['uid'],
                    'prompt': ask_request.prompt,
                    'response': f"Error: {str(e)}",
                    'type': ask_request.type,
                    'timestamp': datetime.now(),
                    'success': False,
                    'error': str(e)
                }
            )
        except Exception as db_error:
            logger.error(f"Failed to save error to history: {db_error}")

        # Return appropriate status code based on error type
        if "API key" in str(e) or "authentication" in str(e):
            raise HTTPException(status_code=401, detail=str(e))
        elif "quota" in str(e) or "limit" in str(e):
            raise HTTPException(status_code=429, detail=str(e))
        elif "model" in str(e) or "not found" in str(e):
            raise HTTPException(status_code=503, detail=str(e))
        else:
            raise HTTPException(status_code=500, detail=str(e))

@router.post("/stream")
async def stream_endpoint(ask_request: AskRequest, user=Depends(get_current_user)):
    """Streaming endpoint for real-time responses"""
    try:
        if not ask_request.prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")

        async def generate_stream():
            try:
                # Send initial event
                yield f"data: {json.dumps({'type': 'start', 'timestamp': datetime.now().isoformat()})}\n\n"
                
                response = await gemini_service.generate_text(ask_request.prompt)
                
                # Simulate streaming by sending chunks
                words = response.split(' ')
                current_text = ''
                
                for i, word in enumerate(words):
                    current_text += (' ' if i > 0 else '') + word
                    
                    yield f"data: {json.dumps({
                        'type': 'chunk',
                        'content': current_text,
                        'progress': (i + 1) / len(words)
                    })}\n\n"
                    
                    await asyncio.sleep(0.05)  # Small delay
                
                # Send completion event
                yield f"data: {json.dumps({
                    'type': 'complete',
                    'content': response,
                    'timestamp': datetime.now().isoformat()
                })}\n\n"
                
            except Exception as e:
                yield f"data: {json.dumps({
                    'type': 'error',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })}\n\n"

        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control"
            }
        )
        
    except Exception as e:
        logger.error(f"Stream endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))