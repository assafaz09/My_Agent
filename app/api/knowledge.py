from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime

from app.models.knowledge import KnowledgeDocument, KnowledgeSearchResult, PersonalProfile
from app.services.qdrant_service import QdrantService
from app.core.agent import PersonalAgent

router = APIRouter()

# Global service instances
qdrant_service = QdrantService()
agent = PersonalAgent()

@router.get("/", response_model=List[KnowledgeDocument])
async def list_knowledge():
    """List all uploaded knowledge documents"""
    try:
        documents = await qdrant_service.get_all_documents()
        return documents
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search", response_model=List[KnowledgeSearchResult])
async def search_knowledge(
    query: str = Query(..., description="Search query"),
    limit: int = Query(5, description="Maximum number of results"),
    threshold: float = Query(0.7, description="Minimum similarity threshold")
):
    """Search through personal knowledge"""
    try:
        results = await qdrant_service.search_knowledge(
            query=query,
            limit=limit,
            threshold=threshold
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/profile", response_model=PersonalProfile)
async def get_personal_profile():
    """Get the agent's understanding of you"""
    try:
        profile = await agent.build_personal_profile()
        return profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{document_id}")
async def delete_knowledge(document_id: str):
    """Remove a knowledge document"""
    try:
        success = await qdrant_service.delete_document(document_id)
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
        stats = await qdrant_service.get_collection_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
