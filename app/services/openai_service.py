from openai import AsyncOpenAI
from typing import List, Dict, Any, Optional
import json
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.embedding_model = settings.openai_embedding_model
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """Get chat completion from OpenAI"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI chat completion error: {e}")
            raise
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        try:
            response = await self.client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}")
            raise
    
    async def extract_knowledge(self, text: str, file_type: str) -> Dict[str, Any]:
        """Extract structured knowledge from text using GPT-4"""
        system_prompt = f"""
        You are a knowledge extraction specialist. Analyze the following text and extract personal information.
        Focus on identifying:
        1. Personal relationships (family, friends, colleagues)
        2. Important events and memories
        3. Personal preferences and habits
        4. Communication style and expressions
        5. Emotional patterns and triggers
        6. Goals and aspirations
        7. Cultural background and values
        8. Language preferences (Hebrew/English usage)

        Return a JSON object with these categories. If no information exists for a category, return an empty list or object.
        """
        
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"File type: {file_type}\n\nContent:\n{text}"}
            ]
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.1,  # Lower temperature for structured extraction
                max_tokens=2000
            )
            
            # Parse the JSON response
            content = response.choices[0].message.content
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # If response is not valid JSON, try to extract JSON from the text
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    # Fallback: return basic structure
                    return {
                        "relationships": [],
                        "events": [],
                        "preferences": [],
                        "communication_style": {},
                        "emotional_patterns": [],
                        "goals_aspirations": [],
                        "cultural_background": {},
                        "languages": []
                    }
                    
        except Exception as e:
            logger.error(f"Knowledge extraction error: {e}")
            # Return empty structure on error
            return {
                "relationships": [],
                "events": [],
                "preferences": [],
                "communication_style": {},
                "emotional_patterns": [],
                "goals_aspirations": [],
                "cultural_background": {},
                "languages": []
            }
    
    async def analyze_language(self, text: str) -> str:
        """Detect if text is primarily Hebrew or English"""
        try:
            hebrew_chars = len([c for c in text if '\u0590' <= c <= '\u05FF'])
            english_chars = len([c for c in text if c.isalpha() and c.isascii()])
            
            if hebrew_chars > english_chars:
                return "he"
            else:
                return "en"
        except:
            return "en"  # Default to English
