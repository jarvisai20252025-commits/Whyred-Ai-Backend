import httpx
import os
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class SearchService:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
        self.search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
        self.base_url = "https://www.googleapis.com/customsearch/v1"

    async def search_with_ai(self, query: str) -> Dict[str, Any]:
        """Perform Google Custom Search and return results with context"""
        try:
            async with httpx.AsyncClient() as client:
                params = {
                    "key": self.api_key,
                    "cx": self.search_engine_id,
                    "q": query,
                    "num": 5
                }
                
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                
                data = response.json()
                results = []
                context = ""
                
                if "items" in data:
                    for item in data["items"]:
                        result = {
                            "title": item.get("title", ""),
                            "link": item.get("link", ""),
                            "snippet": item.get("snippet", "")
                        }
                        results.append(result)
                        context += f"Title: {result['title']}\nSnippet: {result['snippet']}\n\n"
                
                return {
                    "results": results,
                    "context": context
                }
                
        except Exception as e:
            logger.error(f"Search error: {e}")
            return {
                "results": [],
                "context": f"Search functionality is currently unavailable for query: {query}"
            }

# Global instance
search_service = SearchService()