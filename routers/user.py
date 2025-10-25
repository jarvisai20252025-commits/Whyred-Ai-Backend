from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import asyncio
from datetime import datetime
import logging

from middleware.auth import get_current_user
from services.firebase_service import get_firestore_client

logger = logging.getLogger(__name__)
router = APIRouter()

class UserProfile(BaseModel):
    displayName: str = None
    email: str = None
    preferences: dict = {}

@router.get("/profile")
async def get_user_profile(user=Depends(get_current_user)):
    """Get user profile"""
    try:
        db = get_firestore_client()
        user_doc = await asyncio.to_thread(
            db.collection('users').document(user['uid']).get
        )
        
        if user_doc.exists:
            profile_data = user_doc.to_dict()
            return {
                "uid": user['uid'],
                "email": user.get('email'),
                "displayName": profile_data.get('displayName'),
                "preferences": profile_data.get('preferences', {}),
                "createdAt": profile_data.get('createdAt'),
                "lastActive": profile_data.get('lastActive')
            }
        else:
            # Create new user profile
            profile_data = {
                "uid": user['uid'],
                "email": user.get('email'),
                "displayName": user.get('name'),
                "preferences": {},
                "createdAt": datetime.now(),
                "lastActive": datetime.now()
            }
            
            await asyncio.to_thread(
                db.collection('users').document(user['uid']).set,
                profile_data
            )
            
            return profile_data
            
    except Exception as e:
        logger.error(f"Get profile error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/profile")
async def update_user_profile(profile: UserProfile, user=Depends(get_current_user)):
    """Update user profile"""
    try:
        db = get_firestore_client()
        
        update_data = {
            "lastActive": datetime.now()
        }
        
        if profile.displayName is not None:
            update_data["displayName"] = profile.displayName
        if profile.preferences:
            update_data["preferences"] = profile.preferences
            
        await asyncio.to_thread(
            db.collection('users').document(user['uid']).update,
            update_data
        )
        
        return {"message": "Profile updated successfully"}
        
    except Exception as e:
        logger.error(f"Update profile error: {e}")
        raise HTTPException(status_code=500, detail=str(e))