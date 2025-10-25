import firebase_admin
from firebase_admin import credentials, firestore, auth
import os
import json

def init_firebase():
    """Initialize Firebase Admin SDK"""
    if not firebase_admin._apps:
        service_account_info = {
            "type": "service_account",
            "project_id": os.getenv("FIREBASE_PROJECT_ID"),
            "private_key": os.getenv("FIREBASE_PRIVATE_KEY", "").replace("\\n", "\n"),
            "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
        }
        
        cred = credentials.Certificate(service_account_info)
        firebase_admin.initialize_app(cred, {
            'projectId': os.getenv("FIREBASE_PROJECT_ID")
        })

def get_firestore_client():
    """Get Firestore client"""
    return firestore.client()

def get_auth_client():
    """Get Firebase Auth client"""
    return auth