from typing import List, Dict, Any, Optional
import json
import logging
from datetime import datetime

from app.services.openai_service import OpenAIService
from app.services.qdrant_service import QdrantService
from app.core.prompts import SystemPrompts
from app.core.config import settings
from app.models.chat import ChatMessage
from app.models.knowledge import PersonalProfile

logger = logging.getLogger(__name__)

class PersonalAgent:
    def __init__(self):
        self.openai_service = OpenAIService()
        self.qdrant_service = QdrantService()
        self.personal_profile_cache = None
        self.profile_cache_timestamp = None
    
    async def chat(
        self, 
        message: str, 
        conversation_history: List[ChatMessage], 
        language: str = "en"
    ) -> Dict[str, Any]:
        """Generate response using knowledge base and personal context"""
        try:
            # Generate embedding for user message
            message_embedding = await self.openai_service.generate_embedding(message)
            
            # Search knowledge base
            relevant_knowledge = await self.qdrant_service.search_knowledge(
                query=message,
                embedding=message_embedding,
                limit=settings.max_knowledge_results
            )
            
            # Get personal profile
            personal_profile = await self._get_personal_profile()
            
            # Build system prompt
            system_prompt = await self._build_system_prompt(
                personal_profile=personal_profile,
                relevant_knowledge=relevant_knowledge,
                language=language,
                conversation_history=conversation_history
            )
            
            # Prepare messages for OpenAI
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ]
            
            # Add conversation history
            for chat_msg in conversation_history[-10:]:  # Last 10 messages
                messages.append({
                    "role": chat_msg.role,
                    "content": chat_msg.content
                })
            
            # Generate response
            response = await self.openai_service.chat_completion(
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            # Detect response language
            response_language = await self.openai_service.analyze_language(response)
            
            return {
                "response": response,
                "language": response_language,
                "sources": [chunk.document_id for chunk in relevant_knowledge],
                "personal_context_used": len(relevant_knowledge) > 0,
                "search_method": "knowledge_base" if relevant_knowledge else "no_knowledge"
            }
            
        except Exception as e:
            logger.error(f"Chat error: {e}")
            raise
    
    async def _get_personal_profile(self) -> PersonalProfile:
        """Get or build personal profile"""
        try:
            # Check cache (cache for 1 hour)
            if (self.personal_profile_cache and 
                self.profile_cache_timestamp and 
                (datetime.now() - self.profile_cache_timestamp).seconds < 3600):
                return self.personal_profile_cache
            
            # Build profile from knowledge base
            profile = await self.build_personal_profile()
            
            # Cache the profile
            self.personal_profile_cache = profile
            self.profile_cache_timestamp = datetime.now()
            
            return profile
            
        except Exception as e:
            logger.error(f"Error getting personal profile: {e}")
            # Return empty profile on error
            return PersonalProfile(
                profile_id="error",
                last_updated=datetime.now()
            )
    
    async def build_personal_profile(self) -> PersonalProfile:
        """Build comprehensive personal profile from knowledge base"""
        try:
            # Get all documents
            documents = await self.qdrant_service.get_all_documents()
            
            # Aggregate knowledge from all documents
            all_knowledge = {
                "relationships": [],
                "events": [],
                "preferences": [],
                "communication_style": {},
                "emotional_patterns": [],
                "goals_aspirations": [],
                "cultural_background": {},
                "languages": []
            }
            
            for doc in documents:
                if "extracted_knowledge" in doc.metadata:
                    knowledge = doc.metadata["extracted_knowledge"]
                    
                    # Merge knowledge
                    for key in all_knowledge:
                        if key in knowledge and knowledge[key]:
                            if isinstance(knowledge[key], list):
                                all_knowledge[key].extend(knowledge[key])
                            else:
                                all_knowledge[key].update(knowledge[key])
            
            # Create profile
            profile = PersonalProfile(
                profile_id="main_profile",
                relationships=self._deduplicate_list(all_knowledge["relationships"]),
                important_events=self._deduplicate_list(all_knowledge["events"]),
                preferences=self._deduplicate_list(all_knowledge["preferences"]),
                communication_style=all_knowledge["communication_style"],
                emotional_patterns=self._deduplicate_list(all_knowledge["emotional_patterns"]),
                goals_aspirations=self._deduplicate_list(all_knowledge["goals_aspirations"]),
                cultural_background=all_knowledge["cultural_background"],
                languages=list(set(all_knowledge["languages"] + ["en", "he"])),  # Default languages
                last_updated=datetime.now()
            )
            
            return profile
            
        except Exception as e:
            logger.error(f"Error building personal profile: {e}")
            return PersonalProfile(
                profile_id="error",
                last_updated=datetime.now()
            )
    
    async def _build_system_prompt(
        self,
        personal_profile: PersonalProfile,
        relevant_knowledge: List,
        language: str,
        conversation_history: List[ChatMessage]
    ) -> str:
        """Build comprehensive system prompt using street language and strict knowledge rules"""
        
        # Choose the right persona based on language
        if language == "he":
            base_persona = SystemPrompts.STREET_HEBREW_PERSONA
        else:
            base_persona = SystemPrompts.STREET_ENGLISH_PERSONA
        
        # Add strict knowledge rule
        strict_rule = SystemPrompts.STRICT_KNOWLEDGE_RULE
        
        # Build relevant knowledge context about Assaf
        knowledge_context = ""
        if relevant_knowledge:
            knowledge_context = "\n\nמידע שיש לי על אסף מהמסמכים:\n" if language == "he" else "\n\nInformation I have about Assaf from documents:\n"
            for i, chunk in enumerate(relevant_knowledge, 1):
                knowledge_context += f"{i}. {chunk.content}\n"
        else:
            knowledge_context = "\n\nאין לי מידע ספציפי על זה מהמסמכים של אסף." if language == "he" else "\n\nI don't have specific information about this from Assaf's documents."
        
        # Build conversation context
        conversation_context = ""
        if conversation_history:
            conversation_context = "\n\nשיחה קודמת:\n" if language == "he" else "\n\nPrevious conversation:\n"
            for msg in conversation_history[-3:]:  # Last 3 messages
                role_name = "משתמש" if msg.role == "user" else "אני"
                if language != "he":
                    role_name = "User" if msg.role == "user" else "Me"
                conversation_context += f"{role_name}: {msg.content}\n"
        
        # Complete system prompt
        system_prompt = f"""
{base_persona}

{strict_rule}

{knowledge_context}

{conversation_context}

תזכור: אתה חבר אמיתי של אסף, לא AI. דבר בצורה טבעית, בלי פורמליות מיותרת.
"""
        
        return system_prompt
    
    def _deduplicate_list(self, items: List) -> List:
        """Remove duplicates from list while preserving order"""
        seen = set()
        result = []
        for item in items:
            if isinstance(item, dict):
                # For dictionaries, use string representation for comparison
                item_str = json.dumps(item, sort_keys=True, ensure_ascii=False)
                if item_str not in seen:
                    seen.add(item_str)
                    result.append(item)
            else:
                if item not in seen:
                    seen.add(item)
                    result.append(item)
        return result
