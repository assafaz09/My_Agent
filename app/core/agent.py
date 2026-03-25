from typing import List, Dict, Any, Optional
import json
import logging
import textwrap
from datetime import datetime

from app.services.openai_service import OpenAIService
from app.services.vector_db import get_vector_db
from app.core.prompts import SystemPrompts, PersonaTraits
from app.core.config import settings
from app.models.chat import ChatMessage
from app.models.knowledge import PersonalProfile

logger = logging.getLogger(__name__)

class PersonalAgent:
    def __init__(self):
        self.openai_service = OpenAIService()
        self.vector_db = get_vector_db()
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
            try:
                message_embedding = await self.openai_service.generate_embedding(message)
            except Exception as e:
                # If OpenAI isn't configured/available, return a safe response.
                logger.error(f"OpenAI embedding failed, returning fallback response: {e}")
                fallback_response = (
                    "וואלה כרגע אני לא מצליח לענות כי שירות ה-AI לא זמין אצלנו. נסה שוב עוד רגע."
                    if language == "he"
                    else "Right now I can't answer because the AI service isn't available. Try again in a moment."
                )
                return {
                    "response": fallback_response,
                    "language": language,
                    "sources": [],
                    "personal_context_used": False,
                    "search_method": "no_knowledge",
                }
            
            # Search knowledge base
            try:
                relevant_knowledge = await self.vector_db.search_knowledge(
                    query=message,
                    embedding=message_embedding,
                    limit=settings.max_knowledge_results
                )
            except Exception as e:
                # In production environments (e.g. serverless), the vector DB might be unreachable.
                # Don't crash the whole function; fall back to "no knowledge".
                logger.error(f"Vector DB search failed, falling back to empty knowledge: {e}")
                relevant_knowledge = []
            
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
            try:
                response = await self.openai_service.chat_completion(
                    messages=messages,
                    temperature=0.4,
                    max_tokens=450
                )
            except Exception as e:
                logger.error(f"OpenAI chat completion failed, returning fallback response: {e}")
                fallback_response = (
                    "וואלה כרגע אני לא מצליח לגבש תשובה. נסה שוב עוד רגע."
                    if language == "he"
                    else "Right now I can't generate a response. Try again in a moment."
                )
                return {
                    "response": fallback_response,
                    "language": language,
                    "sources": [],
                    "personal_context_used": False,
                    "search_method": "no_knowledge",
                }
            
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
            # Last-resort: never crash the serverless handler.
            logger.error(f"Chat error (last-resort fallback): {e}")
            fallback_response = (
                "וואלה משהו השתבש בצד שלנו. נסה שוב עוד רגע."
                if language == "he"
                else "Something went wrong on our side. Try again in a moment."
            )
            return {
                "response": fallback_response,
                "language": language,
                "sources": [],
                "personal_context_used": False,
                "search_method": "no_knowledge",
            }
    
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
            documents = await self.vector_db.get_all_documents()
            
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
            strict_rule = SystemPrompts.STRICT_KNOWLEDGE_RULE
        else:
            base_persona = SystemPrompts.STREET_ENGLISH_PERSONA
            strict_rule = SystemPrompts.STRICT_KNOWLEDGE_RULE_EN
        
        # Build relevant knowledge context about Assaf
        knowledge_context = ""
        if relevant_knowledge:
            knowledge_context = "\n\nמידע שיש לי על אסף מהמסמכים:\n" if language == "he" else "\n\nInformation I have about Assaf from documents:\n"
            for i, chunk in enumerate(relevant_knowledge, 1):
                knowledge_context += f"{i}. {chunk.content}\n"
        else:
            knowledge_context = "\n\וואלה התקלת אותי אני לא יודע את התשובה אני אבדוק את זה " if language == "he" else "\n\nI don't have specific information about this from Assaf's documents."

        # Tone snippets (style-only). Never present these as facts.
        if language == "he":
            tone_phrases = (
                PersonaTraits.STREET_COMMUNICATION_STYLES["casual"]["about_assaf"][:2]
                + PersonaTraits.STREET_COMMUNICATION_STYLES["assaf_isms"]["expressions"][:2]
                + PersonaTraits.STREET_COMMUNICATION_STYLES["assaf_isms"]["vibe_checks"][:1]
            )
            tone_intro = "אם מתאים, אפשר לשזור ביטוי קצר אחד מהוייבים האלה (סטייל בלבד):"
        else:
            # Pick English phrases from the same style lists (style-only).
            tone_phrases = (
                PersonaTraits.STREET_COMMUNICATION_STYLES["casual"]["about_assaf"][3:5]
                + PersonaTraits.STREET_COMMUNICATION_STYLES["assaf_isms"]["expressions"][4:6]
                + PersonaTraits.STREET_COMMUNICATION_STYLES["assaf_isms"]["vibe_checks"][3:4]
            )
            tone_intro = "If it fits, you can weave ONE short phrase from these vibe lines (style-only):"

        tone_context = "\n".join([f"- {p}" for p in tone_phrases])
        tone_fact_disclaimer = (
            "אלה ביטויי סטייל בלבד. אל תציג אותם כעובדות על אסף שלא מופיעות במסמכים."
            if language == "he"
            else "These are style-only phrases. Do NOT present them as facts about Assaf that aren't backed by the documents."
        )
        
        # Build conversation context
        conversation_context = ""
        if conversation_history:
            conversation_context = "\n\nשיחה קודמת:\n" if language == "he" else "\n\nPrevious conversation:\n"
            for msg in conversation_history[-3:]:  # Last 3 messages
                role_name = "משתמש" if msg.role == "user" else "אני"
                if language != "he":
                    role_name = "User" if msg.role == "user" else "Me"
                conversation_context += f"{role_name}: {msg.content}\n"

        grounding_line = (
            "תזכור: אתה חבר אמיתי של אסף, לא AI. דבר בצורה טבעית, בלי פורמליות מיותרת."
            if language == "he"
            else "Remember: you're Assaf's real friend, not an AI. Be natural and casual, without corporate formalities."
        )

        # Complete system prompt
        system_prompt = textwrap.dedent(
            f"""
            {base_persona}

            {strict_rule}

            {tone_intro}
            {tone_context}
            {tone_fact_disclaimer}

            {knowledge_context}

            {conversation_context}

            {grounding_line}
            """
        ).strip()
        
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
