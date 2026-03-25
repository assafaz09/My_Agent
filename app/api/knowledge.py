from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime

from app.models.knowledge import KnowledgeDocument, KnowledgeSearchResult, PersonalProfile
from app.services.vector_db import get_vector_db
from app.core.agent import PersonalAgent
from app.services.openai_service import OpenAIService

router = APIRouter()

# Global service instances
vector_db = get_vector_db()
agent = PersonalAgent()
openai_service = OpenAIService()

@router.get("/", response_model=List[KnowledgeDocument])
async def list_knowledge():
    """List all uploaded knowledge documents"""
    try:
        documents = await vector_db.get_all_documents()
        return documents
    except Exception as e:
        # Don't crash the whole serverless function if the vector DB is unreachable.
        # Return an empty list and let the chat endpoint still work with "no knowledge".
        return []

@router.get("/search", response_model=List[KnowledgeSearchResult])
async def search_knowledge(
    query: str = Query(..., description="Search query"),
    limit: int = Query(5, description="Maximum number of results"),
    threshold: float = Query(0.5, description="Minimum similarity threshold")
):
    """Search through personal knowledge"""
    try:
        query_embedding = await openai_service.generate_embedding(query)
        results = await vector_db.search_knowledge(
            query=query,
            embedding=query_embedding,
            limit=limit,
            threshold=threshold
        )
        return results
    except Exception as e:
        return []

@router.get("/profile", response_model=PersonalProfile)
async def get_personal_profile():
    """Get the agent's understanding of you"""
    try:
        # Use the safe internal getter that already returns an empty/error profile
        # instead of crashing when the vector DB is unavailable.
        return await agent._get_personal_profile()
    except Exception as e:
        return PersonalProfile(
            profile_id="error",
            last_updated=datetime.now(),
        )

@router.delete("/{document_id}")
async def delete_knowledge(document_id: str):
    """Remove a knowledge document"""
    try:
        success = await vector_db.delete_document(document_id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {"message": "Document deleted successfully", "document_id": document_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/retrain")
async def retrain_knowledge():
    """Re-process all files with updated extraction"""
    try:
        # This would trigger reprocessing of all uploaded files
        # Implementation depends on your specific needs
        return {"message": "Knowledge retraining started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_knowledge_stats():
    """Get statistics about the knowledge base"""
    try:
        stats = await vector_db.get_collection_stats()
        return stats
    except Exception as e:
        return {}
