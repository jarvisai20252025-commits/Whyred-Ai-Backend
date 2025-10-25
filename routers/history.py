from fastapi import APIRouter, HTTPException, Depends, Query
import asyncio
from datetime import datetime
import logging

from middleware.auth import get_current_user
from services.firebase_service import get_firestore_client

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/")
async def get_chat_history(
    user=Depends(get_current_user),
    limit: int = Query(50, ge=1, le=100)
):
    """Get chat history for user"""
    try:
        db = get_firestore_client()
        
        # Get chat history ordered by timestamp
        query = db.collection('chat_history')\
                 .where('userId', '==', user['uid'])\
                 .order_by('timestamp', direction='DESCENDING')\
                 .limit(limit)
        
        docs = await asyncio.to_thread(query.get)
        
        history = []
        for doc in docs:
            data = doc.to_dict()
            # Convert timestamp to ISO string if it exists
            if 'timestamp' in data and data['timestamp']:
                data['timestamp'] = data['timestamp'].isoformat()
            history.append({
                'id': doc.id,
                **data
            })
        
        return {"history": history}
        
    except Exception as e:
        logger.error(f"Get history error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/")
async def clear_chat_history(user=Depends(get_current_user)):
    """Clear all chat history for user"""
    try:
        db = get_firestore_client()
        
        # Get all user's chat history documents
        query = db.collection('chat_history').where('userId', '==', user['uid'])
        docs = await asyncio.to_thread(query.get)
        
        # Delete all documents in batches
        batch = db.batch()
        count = 0
        
        for doc in docs:
            batch.delete(doc.reference)
            count += 1
            
            # Commit batch every 500 operations (Firestore limit)
            if count % 500 == 0:
                await asyncio.to_thread(batch.commit)
                batch = db.batch()
        
        # Commit remaining operations
        if count % 500 != 0:
            await asyncio.to_thread(batch.commit)
        
        return {"message": f"Cleared {count} chat history entries"}
        
    except Exception as e:
        logger.error(f"Clear history error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{history_id}")
async def delete_chat_entry(history_id: str, user=Depends(get_current_user)):
    """Delete specific chat history entry"""
    try:
        db = get_firestore_client()
        
        # Verify the document belongs to the user
        doc_ref = db.collection('chat_history').document(history_id)
        doc = await asyncio.to_thread(doc_ref.get)
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Chat entry not found")
        
        doc_data = doc.to_dict()
        if doc_data.get('userId') != user['uid']:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Delete the document
        await asyncio.to_thread(doc_ref.delete)
        
        return {"message": "Chat entry deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete chat entry error: {e}")
        raise HTTPException(status_code=500, detail=str(e))