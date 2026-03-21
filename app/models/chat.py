from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = datetime.now()
    
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    language: Optional[str] = "en"  # "en" or "he"
    
class ChatResponse(BaseModel):
    response: str
    session_id: str
    language: str
    sources: List[str] = []
    timestamp: datetime = datetime.now()

class ConversationSession(BaseModel):
    session_id: str
    messages: List[ChatMessage]
    created_at: datetime
    last_activity: datetime
    language: str = "en"
