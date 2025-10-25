from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import asyncio
from datetime import datetime
import logging

from middleware.auth import get_current_user
from services.search_service import search_service
from services.gemini_service import gemini_service
from services.firebase_service import get_firestore_client

logger = logging.getLogger(__name__)
router = APIRouter()

class SearchRequest(BaseModel):
    query: str

@router.post("/")
async def search_endpoint(search_request: SearchRequest, user=Depends(get_current_user)):
    """Google Custom Search integration"""
    try:
        if not search_request.query:
            raise HTTPException(status_code=400, detail="Search query is required")

        # Get search results
        search_data = await search_service.search_with_ai(search_request.query)
        
        # Generate AI response based on search results
        ai_prompt = f"Based on the following search results, provide a comprehensive answer to: \"{search_request.query}\"\n\nSearch Results:\n{search_data['context']}"
        ai_response = await gemini_service.generate_text(ai_prompt)
        
        # Save to history
        try:
            db = get_firestore_client()
            await asyncio.to_thread(
                db.collection('chat_history').add,
                {
                    'userId': user['uid'],
                    'prompt': search_request.query,
                    'response': ai_response,
                    'searchResults': search_data['results'],
                    'type': 'search',
                    'timestamp': datetime.now()
                }
            )
        except Exception as db_error:
            logger.error(f"Failed to save search to history: {db_error}")

        return {
            "response": ai_response,
            "sources": search_data['results']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))