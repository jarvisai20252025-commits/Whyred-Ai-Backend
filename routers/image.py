from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import asyncio
from datetime import datetime
import logging

from middleware.auth import get_current_user
from services.gemini_service import gemini_service
from services.firebase_service import get_firestore_client

logger = logging.getLogger(__name__)
router = APIRouter()

class ImageRequest(BaseModel):
    prompt: str
    imageData: str = None
    mimeType: str = "image/jpeg"

@router.post("/")
async def image_endpoint(image_request: ImageRequest, user=Depends(get_current_user)):
    """Image analysis endpoint"""
    try:
        if not image_request.prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")

        processing_start = datetime.now()
        
        if image_request.imageData:
            # Analyze image with prompt
            response = await gemini_service.generate_from_image(
                image_request.prompt, 
                image_request.imageData, 
                image_request.mimeType
            )
        else:
            # Generate image-related response without actual image
            response = await gemini_service.generate_text(
                f"Regarding images and the following request: {image_request.prompt}"
            )

        processing_time = (datetime.now() - processing_start).total_seconds() * 1000
        
        # Save to history
        try:
            db = get_firestore_client()
            await asyncio.to_thread(
                db.collection('chat_history').add,
                {
                    'userId': user['uid'],
                    'prompt': image_request.prompt,
                    'response': response,
                    'type': 'image',
                    'hasImage': bool(image_request.imageData),
                    'timestamp': datetime.now(),
                    'processingTime': processing_time,
                    'success': True
                }
            )
        except Exception as db_error:
            logger.error(f"Failed to save image request to history: {db_error}")

        return {
            "response": response,
            "timestamp": datetime.now().isoformat(),
            "processingTime": processing_time,
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))