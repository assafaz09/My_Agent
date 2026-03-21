from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import uuid
from datetime import datetime

from app.models.chat import ChatRequest, ChatResponse, ChatMessage
from app.core.agent import PersonalAgent
from app.core.config import settings

router = APIRouter()

# In-memory session storage (in production, use Redis or database)
sessions: dict = {}

# Global agent instance
agent = PersonalAgent()

async def get_session(session_id: Optional[str] = None) -> str:
    """Get or create a conversation session"""
    if session_id and session_id in sessions:
        sessions[session_id]["last_activity"] = datetime.now()
        return session_id
    
    new_session_id = str(uuid.uuid4())
    sessions[new_session_id] = {
        "messages": [],
        "created_at": datetime.now(),
        "last_activity": datetime.now(),
        "language": "en"
    }
    return new_session_id

@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message and get response from the personal agent"""
    try:
        session_id = await get_session(request.session_id)
        
        # Update session language if specified
        if request.language:
            sessions[session_id]["language"] = request.language
        
        # Get conversation history
        conversation_history = sessions[session_id]["messages"][-settings.max_conversation_length:]
        
        # Get response from agent
        response_data = await agent.chat(
            message=request.message,
            conversation_history=conversation_history,
            language=request.language or sessions[session_id]["language"]
        )
        
        # Store messages in session
        user_message = ChatMessage(role="user", content=request.message)
        assistant_message = ChatMessage(role="assistant", content=response_data["response"])
        
        sessions[session_id]["messages"].extend([user_message, assistant_message])
        sessions[session_id]["last_activity"] = datetime.now()
        
        return ChatResponse(
            response=response_data["response"],
            session_id=session_id,
            language=response_data.get("language", request.language or "en"),
            sources=response_data.get("sources", [])
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions")
async def list_sessions():
    """List all active sessions"""
    return {
        "sessions": [
            {
                "session_id": sid,
                "created_at": data["created_at"].isoformat(),
                "last_activity": data["last_activity"].isoformat(),
                "message_count": len(data["messages"]),
                "language": data["language"]
            }
            for sid, data in sessions.items()
        ]
    }

@router.post("/sessions/{session_id}/reset")
async def reset_session(session_id: str):
    """Reset conversation context for a session"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    sessions[session_id]["messages"] = []
    sessions[session_id]["last_activity"] = datetime.now()
    
    return {"message": "Session reset successfully", "session_id": session_id}
