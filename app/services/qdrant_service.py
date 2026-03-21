from qdrant_client import QdrantClient, AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from typing import List, Dict, Any, Optional
import uuid
import logging
from datetime import datetime

from app.core.config import settings
from app.models.knowledge import KnowledgeDocument, KnowledgeChunk, KnowledgeSearchResult

logger = logging.getLogger(__name__)

class QdrantService:
    def __init__(self):
        self.client = AsyncQdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port
        )
        self.collection_name = settings.qdrant_collection_name
    
    async def initialize_collection(self):
        """Initialize Qdrant collection if it doesn't exist"""
        try:
            collections = await self.client.get_collections()
            collection_exists = any(
                collection.name == self.collection_name 
                for collection in collections.collections
            )
            
            if not collection_exists:
                await self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=1536,  # OpenAI embedding size
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created collection: {self.collection_name}")
            else:
                logger.info(f"Collection {self.collection_name} already exists")
        except Exception as e:
            logger.error(f"Error initializing collection: {e}")
            # Don't raise - continue with existing collection
    
    async def add_document(self, document: KnowledgeDocument) -> str:
        """Add a document and its chunks to the vector database"""
        try:
            await self.initialize_collection()
            
            # Split document into chunks
            chunks = self._chunk_text(document.content)
            
            points = []
            for i, chunk_text in enumerate(chunks):
                chunk_id = f"{document.document_id}_chunk_{i}"
                
                # Create metadata
                metadata = {
                    "document_id": document.document_id,
                    "filename": document.filename,
                    "file_type": document.file_type,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    **document.metadata
                }
                
                point = PointStruct(
                    id=chunk_id,
                    vector=[],  # Will be populated when embedding is generated
                    payload={
                        "content": chunk_text,
                        "metadata": metadata,
                        "created_at": datetime.now().isoformat()
                    }
                )
                points.append(point)
            
            # Add points to collection
            await self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            logger.info(f"Added document {document.document_id} with {len(chunks)} chunks")
            return document.document_id
            
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            raise
    
    async def add_chunks_with_embeddings(self, chunks: List[KnowledgeChunk]):
        """Add chunks with pre-computed embeddings"""
        try:
            # Try to initialize collection, but continue even if it fails
            try:
                await self.initialize_collection()
            except Exception as e:
                logger.warning(f"Could not initialize collection, assuming it exists: {e}")
            
            points = []
            for chunk in chunks:
                point = PointStruct(
                    id=chunk.chunk_id,
                    vector=chunk.embedding,
                    payload={
                        "content": chunk.content,
                        "metadata": chunk.metadata,
                        "created_at": chunk.created_at.isoformat()
                    }
                )
                points.append(point)
            
            await self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            logger.info(f"Added {len(chunks)} chunks to collection")
            
        except Exception as e:
            logger.error(f"Error adding chunks: {e}")
            raise
    
    async def search_knowledge(
        self, 
        query: str, 
        embedding: List[float],
        limit: int = 5, 
        threshold: float = 0.7
    ) -> List[KnowledgeSearchResult]:
        """Search for relevant knowledge chunks"""
        try:
            await self.initialize_collection()
            
            search_result = await self.client.search(
                collection_name=self.collection_name,
                query_vector=embedding,
                query_filter=None,
                limit=limit,
                score_threshold=threshold
            )
            
            results = []
            for hit in search_result:
                result = KnowledgeSearchResult(
                    chunk_id=hit.id,
                    document_id=hit.payload["metadata"]["document_id"],
                    content=hit.payload["content"],
                    score=hit.score,
                    metadata=hit.payload["metadata"]
                )
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching knowledge: {e}")
            raise
    
    async def get_all_documents(self) -> List[KnowledgeDocument]:
        """Get all documents from the collection"""
        try:
            await self.initialize_collection()
            
            # Get all points and group by document_id
            scroll_result = await self.client.scroll(
                collection_name=self.collection_name,
                limit=10000,  # Adjust based on expected size
                with_payload=True,
                with_vectors=False
            )
            
            documents = {}
            for point in scroll_result[0]:
                metadata = point.payload["metadata"]
                document_id = metadata["document_id"]
                
                if document_id not in documents:
                    documents[document_id] = {
                        "document_id": document_id,
                        "filename": metadata["filename"],
                        "file_type": metadata["file_type"],
                        "content": "",
                        "metadata": metadata,
                        "created_at": point.payload["created_at"],
                        "chunks": []
                    }
                
                documents[document_id]["chunks"].append(point.payload["content"])
            
            # Combine chunks into full content
            document_list = []
            for doc_data in documents.values():
                doc_data["content"] = "\n\n".join(doc_data["chunks"])
                document = KnowledgeDocument(**doc_data)
                document_list.append(document)
            
            return document_list
            
        except Exception as e:
            logger.error(f"Error getting documents: {e}")
            raise
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete a document and all its chunks"""
        try:
            await self.initialize_collection()
            
            # Delete all points with this document_id
            filter = Filter(
                must=[
                    FieldCondition(
                        key="metadata.document_id",
                        match=MatchValue(value=document_id)
                    )
                ]
            )
            
            await self.client.delete(
                collection_name=self.collection_name,
                points_selector=filter
            )
            
            logger.info(f"Deleted document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return False
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection"""
        try:
            await self.initialize_collection()
            
            collection_info = await self.client.get_collection(self.collection_name)
            
            return {
                "name": self.collection_name,
                "vectors_count": collection_info.vectors_count,
                "segments_count": collection_info.segments_count,
                "disk_data_size": collection_info.disk_data_size,
                "ram_data_size": collection_info.ram_data_size
            }
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            raise
    
    def _chunk_text(self, text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
        """Split text into chunks"""
        if chunk_size is None:
            chunk_size = settings.chunk_size
        if overlap is None:
            overlap = settings.chunk_overlap
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            if end > len(text):
                end = len(text)
            
            chunks.append(text[start:end])
            
            if end >= len(text):
                break
            
            start = end - overlap
        
        return chunks
