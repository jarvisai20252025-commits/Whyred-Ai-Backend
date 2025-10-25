import google.generativeai as genai
import os
import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.models = {
            "text": "gemini-2.0-flash-exp",
            "vision": "gemini-2.0-flash-exp",
            "code": "gemini-2.0-flash-exp",
            "fallback": "gemini-1.5-flash",
            "alternatives": [
                "gemini-2.0-flash-exp",
                "gemini-2.0-flash",
                "models/gemini-2.0-flash-exp",
                "models/gemini-2.0-flash"
            ]
        }
        self.retry_config = {
            "max_retries": 3,
            "base_delay": 1.0,
            "max_delay": 5.0
        }

    async def generate_text(self, prompt: str, model_type: str = "text") -> str:
        """Generate text response using Gemini"""
        return await self._execute_with_retry(self._generate_text_internal, prompt, model_type)

    async def _generate_text_internal(self, prompt: str, model_type: str) -> str:
        model_name = self.models.get(model_type, self.models["text"])
        logger.info(f"Using model: {model_name} for prompt: {prompt[:50]}...")
        
        models_to_try = [model_name] + self.models["alternatives"] + [self.models["fallback"]]
        last_error = None
        
        for model in models_to_try:
            try:
                generation_config = {
                    "temperature": 0.7,
                    "top_k": 40,
                    "top_p": 0.95,
                    "max_output_tokens": 8192,
                }
                
                safety_settings = [
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                ]
                
                model_instance = genai.GenerativeModel(
                    model_name=model,
                    generation_config=generation_config,
                    safety_settings=safety_settings
                )
                
                response = await asyncio.to_thread(model_instance.generate_content, prompt)
                
                if not response or not response.text:
                    raise Exception("Empty response from Gemini API")
                
                text = response.text
                logger.info(f"Generated response length: {len(text)} using model: {model}")
                return text
                
            except Exception as e:
                last_error = e
                logger.warning(f"Model {model} failed: {e}")
                if "not found" not in str(e) and "404" not in str(e):
                    raise e
        
        raise last_error

    async def generate_from_image(self, prompt: str, image_data: str, mime_type: str = "image/jpeg") -> str:
        """Generate response from image using Gemini Vision"""
        return await self._execute_with_retry(self._generate_from_image_internal, prompt, image_data, mime_type)

    async def _generate_from_image_internal(self, prompt: str, image_data: str, mime_type: str) -> str:
        logger.info(f"Generating image response for: {prompt[:50]}...")
        
        generation_config = {
            "temperature": 0.4,
            "top_k": 32,
            "top_p": 1,
            "max_output_tokens": 4096,
        }
        
        model = genai.GenerativeModel(
            model_name=self.models["vision"],
            generation_config=generation_config
        )
        
        image_part = {
            "mime_type": mime_type,
            "data": image_data
        }
        
        response = await asyncio.to_thread(model.generate_content, [prompt, image_part])
        
        if not response or not response.text:
            raise Exception("Empty response from Gemini Vision API")
        
        return response.text

    async def generate_code(self, prompt: str) -> str:
        """Generate code with enhanced prompt"""
        enhanced_prompt = f"""
You are an expert programmer. Generate clean, well-documented, and efficient code for the following request:

{prompt}

Requirements:
- Include proper error handling
- Add meaningful comments
- Follow best practices
- Provide working, production-ready code
- Include usage examples if applicable

Code:"""
        return await self.generate_text(enhanced_prompt, "code")

    async def generate_search(self, query: str) -> str:
        """Generate search response"""
        search_prompt = f"""
Provide a comprehensive answer for the search query: "{query}"

Include:
- Direct answer to the question
- Key facts and details
- Relevant context and background
- Multiple perspectives if applicable
- Recent developments if relevant

Answer:"""
        return await self.generate_text(search_prompt, "text")

    async def _execute_with_retry(self, operation, *args):
        """Execute operation with retry logic"""
        last_error = None
        
        for attempt in range(1, self.retry_config["max_retries"] + 1):
            try:
                logger.info(f"Attempt {attempt}/{self.retry_config['max_retries']}")
                return await operation(*args)
            except Exception as e:
                last_error = e
                logger.error(f"Attempt {attempt} failed: {e}")
                
                if attempt == self.retry_config["max_retries"]:
                    break
                
                delay = min(
                    self.retry_config["base_delay"] * (2 ** (attempt - 1)),
                    self.retry_config["max_delay"]
                ) + (0.1 * attempt)  # Add jitter
                
                logger.info(f"Retrying in {delay:.1f}s...")
                await asyncio.sleep(delay)
        
        # Try fallback model if all retries failed
        if "model" in str(last_error) or "not found" in str(last_error):
            logger.info("Trying fallback model...")
            try:
                model = genai.GenerativeModel(model_name=self.models["fallback"])
                response = await asyncio.to_thread(model.generate_content, "Hello, are you working?")
                return response.text
            except Exception as fallback_error:
                logger.error(f"Fallback model also failed: {fallback_error}")
        
        raise Exception(f"All attempts failed. Last error: {last_error}")

    async def health_check(self) -> bool:
        """Check if Gemini service is healthy"""
        try:
            response = await self.generate_text("Hello, respond with 'OK' if you are working.")
            return "ok" in response.lower()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    def get_model_info(self) -> dict:
        """Get model information"""
        return {
            "models": self.models,
            "api_key_configured": bool(os.getenv("GEMINI_API_KEY")),
            "retry_config": self.retry_config
        }

# Global instance
gemini_service = GeminiService()