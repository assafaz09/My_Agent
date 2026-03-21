from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class KnowledgeDocument(BaseModel):
    document_id: str
    filename: str
    file_type: str
    content: str
    metadata: Dict[str, Any]
    created_at: datetime
    processed: bool = False
    
class KnowledgeChunk(BaseModel):
    chunk_id: str
    document_id: str
    content: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any]
    created_at: datetime

class PersonalProfile(BaseModel):
    profile_id: str
    name: Optional[str] = None
    relationships: List[Dict[str, str]] = []
    important_events: List[Dict[str, str]] = []
    preferences: List[Dict[str, str]] = []
    communication_style: Dict[str, str] = {}
    emotional_patterns: List[Dict[str, str]] = []
    goals_aspirations: List[Dict[str, str]] = []
    cultural_background: Dict[str, str] = {}
    languages: List[str] = []
    last_updated: datetime

class UploadStatus(BaseModel):
    upload_id: str
    filename: str
    status: str  # "uploading", "processing", "completed", "error"
    progress: float = 0.0
    error_message: Optional[str] = None
    created_at: datetime

class KnowledgeSearchResult(BaseModel):
    chunk_id: str
    document_id: str
    content: str
    score: float
    metadata: Dict[str, Any]
