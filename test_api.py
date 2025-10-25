#!/usr/bin/env python3
"""
Test script for Whyred AI FastAPI backend
"""
import httpx
import asyncio
import json

BASE_URL = "http://localhost:8000"

async def test_endpoints():
    """Test all API endpoints"""
    async with httpx.AsyncClient() as client:
        print("🚀 Testing Whyred AI FastAPI Backend\n")
        
        # Test root endpoint
        try:
            response = await client.get(f"{BASE_URL}/")
            print(f"✅ Root endpoint: {response.status_code}")
            print(f"   Response: {response.json()}\n")
        except Exception as e:
            print(f"❌ Root endpoint failed: {e}\n")
        
        # Test health endpoint
        try:
            response = await client.get(f"{BASE_URL}/health")
            print(f"✅ Health endpoint: {response.status_code}")
            print(f"   Response: {response.json()}\n")
        except Exception as e:
            print(f"❌ Health endpoint failed: {e}\n")
        
        # Test ask health endpoint
        try:
            response = await client.get(f"{BASE_URL}/api/ask/health")
            print(f"✅ Ask health endpoint: {response.status_code}")
            print(f"   Response: {response.json()}\n")
        except Exception as e:
            print(f"❌ Ask health endpoint failed: {e}\n")
        
        # Test ask test endpoint
        try:
            response = await client.post(
                f"{BASE_URL}/api/ask/test",
                json={"prompt": "Hello, this is a test!"}
            )
            print(f"✅ Ask test endpoint: {response.status_code}")
            print(f"   Response: {response.json()}\n")
        except Exception as e:
            print(f"❌ Ask test endpoint failed: {e}\n")

if __name__ == "__main__":
    print("Make sure the FastAPI server is running with: python start.py")
    print("Then run this test script\n")
    asyncio.run(test_endpoints())