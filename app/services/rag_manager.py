"""
RAG Management Interface for Assaf's Agent

This module provides tools to monitor and manage the RAG system performance.
"""

from typing import List, Dict, Any, Optional
import json
import logging
from datetime import datetime

from app.services.enhanced_rag import EnhancedRAGService
from app.services.qdrant_service import QdrantService
from app.services.openai_service import OpenAIService
from app.core.config import settings
from app.models.knowledge import KnowledgeSearchResult

logger = logging.getLogger(__name__)

class RAGManager:
    def __init__(self):
        self.enhanced_rag = EnhancedRAGService()
        self.qdrant_service = QdrantService()
        self.openai_service = OpenAIService()
    
    async def get_rag_stats(self) -> Dict[str, Any]:
        """Get comprehensive RAG system statistics"""
        try:
            # Get basic stats
            documents = await self.qdrant_service.get_all_documents()
            
            # Get collection info
            await self.qdrant_service.initialize_collection()
            collection_info = await self.qdrant_service.client.get_collection(
                collection_name=self.qdrant_service.collection_name
            )
            
            stats = {
                "total_documents": len(documents),
                "total_points": collection_info.points_count,
                "vector_size": collection_info.config.params.vectors.size,
                "distance_metric": collection_info.config.params.vectors.distance,
                "enhanced_rag_initialized": self.enhanced_rag._is_initialized,
                "last_updated": datetime.now().isoformat(),
                "documents_by_type": self._count_documents_by_type(documents),
                "storage_size_mb": self._estimate_storage_size(documents)
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting RAG stats: {e}")
            return {"error": str(e)}
    
    def _count_documents_by_type(self, documents) -> Dict[str, int]:
        """Count documents by file type"""
        type_counts = {}
        for doc in documents:
            file_type = getattr(doc, 'file_type', 'unknown')
            type_counts[file_type] = type_counts.get(file_type, 0) + 1
        return type_counts
    
    def _estimate_storage_size(self, documents) -> float:
        """Estimate storage size in MB"""
        total_chars = sum(len(getattr(doc, 'content', '')) for doc in documents)
        # Rough estimate: 1 char ≈ 1 byte, plus metadata overhead
        size_mb = (total_chars * 1.5) / (1024 * 1024)  # 1.5x for metadata
        return round(size_mb, 2)
    
    async def test_search_performance(
        self, 
        test_queries: List[str]
    ) -> Dict[str, Any]:
        """Test RAG search performance with sample queries"""
        try:
            results = {}
            
            for query in test_queries:
                # Generate embedding
                embedding = await self.openai_service.generate_embedding(query)
                
                # Test different search methods
                start_time = datetime.now()
                
                # Basic semantic search
                semantic_results = await self.qdrant_service.search_knowledge(
                    query=query, embedding=embedding, limit=5
                )
                semantic_time = (datetime.now() - start_time).total_seconds()
                
                # Enhanced hybrid search
                start_time = datetime.now()
                hybrid_results = await self.enhanced_rag.hybrid_search(
                    query=query, embedding=embedding, limit=5
                )
                hybrid_time = (datetime.now() - start_time).total_seconds()
                
                # Multi-query search
                start_time = datetime.now()
                multi_results = await self.enhanced_rag.multi_query_search(
                    query=query, embedding=embedding, limit=5
                )
                multi_time = (datetime.now() - start_time).total_seconds()
                
                results[query] = {
                    "semantic_search": {
                        "results_count": len(semantic_results),
                        "avg_score": sum(r.score for r in semantic_results) / len(semantic_results) if semantic_results else 0,
                        "time_seconds": semantic_time
                    },
                    "hybrid_search": {
                        "results_count": len(hybrid_results),
                        "avg_score": sum(r.score for r in hybrid_results) / len(hybrid_results) if hybrid_results else 0,
                        "time_seconds": hybrid_time
                    },
                    "multi_query_search": {
                        "results_count": len(multi_results),
                        "avg_score": sum(r.score for r in multi_results) / len(multi_results) if multi_results else 0,
                        "time_seconds": multi_time
                    }
                }
            
            return results
            
        except Exception as e:
            logger.error(f"Error testing search performance: {e}")
            return {"error": str(e)}
    
    async def analyze_knowledge_gaps(self, topics: List[str]) -> Dict[str, Any]:
        """Analyze knowledge gaps for specific topics"""
        try:
            gap_analysis = {}
            
            for topic in topics:
                # Search for knowledge about this topic
                embedding = await self.openai_service.generate_embedding(topic)
                results = await self.enhanced_rag.hybrid_search(
                    query=topic, embedding=embedding, limit=10
                )
                
                if not results:
                    gap_analysis[topic] = {
                        "coverage": "none",
                        "suggestion": f"No information found about {topic}. Consider adding documents about this topic."
                    }
                elif len(results) < 3:
                    gap_analysis[topic] = {
                        "coverage": "limited",
                        "suggestion": f"Limited information about {topic}. More detailed documents would be helpful.",
                        "existing_docs": len(results)
                    }
                else:
                    avg_score = sum(r.score for r in results) / len(results)
                    if avg_score < 0.7:
                        gap_analysis[topic] = {
                            "coverage": "low_quality",
                            "suggestion": f"Information about {topic} exists but may not be comprehensive. Consider adding more specific content.",
                            "avg_relevance": avg_score
                        }
                    else:
                        gap_analysis[topic] = {
                            "coverage": "good",
                            "suggestion": f"Good coverage of {topic}.",
                            "avg_relevance": avg_score
                        }
            
            return gap_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing knowledge gaps: {e}")
            return {"error": str(e)}
    
    async def optimize_search_thresholds(self, test_queries: List[str]) -> Dict[str, Any]:
        """Find optimal search thresholds through testing"""
        try:
            threshold_tests = {}
            thresholds = [0.5, 0.6, 0.7, 0.8, 0.9]
            
            for threshold in thresholds:
                threshold_results = []
                
                for query in test_queries:
                    embedding = await self.openai_service.generate_embedding(query)
                    results = await self.qdrant_service.search_knowledge(
                        query=query, embedding=embedding, limit=5, threshold=threshold
                    )
                    
                    threshold_results.append(len(results))
                
                avg_results = sum(threshold_results) / len(threshold_results)
                threshold_tests[str(threshold)] = {
                    "avg_results_per_query": avg_results,
                    "zero_results_rate": sum(1 for r in threshold_results if r == 0) / len(threshold_results)
                }
            
            # Find optimal threshold (balances results and relevance)
            optimal_threshold = 0.7  # Default
            max_score = 0
            
            for threshold, metrics in threshold_tests.items():
                # Score: avg_results - penalty for too many zero results
                score = metrics["avg_results_per_query"] - (metrics["zero_results_rate"] * 2)
                if score > max_score and float(threshold) >= 0.6:  # Don't go too low
                    max_score = score
                    optimal_threshold = float(threshold)
            
            return {
                "threshold_tests": threshold_tests,
                "optimal_threshold": optimal_threshold,
                "recommendation": f"Use threshold {optimal_threshold} for best balance of coverage and relevance"
            }
            
        except Exception as e:
            logger.error(f"Error optimizing thresholds: {e}")
            return {"error": str(e)}
    
    async def rebuild_index(self) -> Dict[str, Any]:
        """Rebuild the RAG index (useful after adding many documents)"""
        try:
            start_time = datetime.now()
            
            # Reinitialize enhanced RAG
            await self.enhanced_rag.initialize()
            
            # Get current documents
            documents = await self.qdrant_service.get_all_documents()
            
            rebuild_info = {
                "documents_processed": len(documents),
                "rebuild_time_seconds": (datetime.now() - start_time).total_seconds(),
                "enhanced_rag_initialized": self.enhanced_rag._is_initialized,
                "timestamp": datetime.now().isoformat()
            }
            
            return rebuild_info
            
        except Exception as e:
            logger.error(f"Error rebuilding index: {e}")
            return {"error": str(e)}
    
    async def export_knowledge_summary(self) -> Dict[str, Any]:
        """Export a summary of all knowledge for review"""
        try:
            documents = await self.qdrant_service.get_all_documents()
            
            summary = {
                "total_documents": len(documents),
                "document_summary": [],
                "key_topics": [],
                "content_overview": ""
            }
            
            # Document summaries
            for doc in documents:
                summary["document_summary"].append({
                    "filename": getattr(doc, 'filename', 'unknown'),
                    "file_type": getattr(doc, 'file_type', 'unknown'),
                    "content_length": len(getattr(doc, 'content', '')),
                    "upload_date": getattr(doc, 'upload_date', None).isoformat() if hasattr(doc, 'upload_date') and doc.upload_date else None,
                    "preview": getattr(doc, 'content', '')[:200] + "..." if len(getattr(doc, 'content', '')) > 200 else getattr(doc, 'content', '')
                })
            
            # Combine all content for topic analysis
            all_content = " ".join([getattr(doc, 'content', '') for doc in documents])
            
            if len(all_content) > 1000:
                summary["content_overview"] = all_content[:1000] + "..."
            else:
                summary["content_overview"] = all_content
            
            return summary
            
        except Exception as e:
            logger.error(f"Error exporting knowledge summary: {e}")
            return {"error": str(e)}
