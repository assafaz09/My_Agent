"""
Enhanced RAG System for Assaf's Agent

This module implements advanced Retrieval-Augmented Generation techniques
to improve the accuracy and relevance of knowledge retrieval.
"""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging
from datetime import datetime

from app.services.openai_service import OpenAIService
from app.services.vector_db import get_vector_db
from app.core.config import settings
from app.models.knowledge import KnowledgeSearchResult

logger = logging.getLogger(__name__)

class EnhancedRAGService:
    def __init__(self):
        self.openai_service = OpenAIService()
        self.vector_db = get_vector_db()
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self._is_initialized = False
    
    async def initialize(self):
        """Initialize the RAG service with existing knowledge"""
        try:
            # Load existing documents to build TF-IDF index
            documents = await self.vector_db.get_all_documents()
            if documents:
                contents = [doc.content for doc in documents]
                self.tfidf_vectorizer.fit_transform(contents)
                self._is_initialized = True
                logger.info(f"Enhanced RAG initialized with {len(documents)} documents")
        except Exception as e:
            logger.warning(f"Failed to initialize enhanced RAG: {e}")
    
    async def hybrid_search(
        self,
        query: str,
        embedding: List[float],
        limit: int = 5,
        threshold: float = 0.6
    ) -> List[KnowledgeSearchResult]:
        """
        Hybrid search combining semantic search with keyword search
        """
        try:
            # 1. Semantic search (existing)
            semantic_results = await self.vector_db.search_knowledge(
                query=query,
                embedding=embedding,
                limit=limit * 2,  # Get more candidates for re-ranking
                threshold=threshold * 0.8  # Lower threshold for more candidates
            )
            
            # 2. Keyword-based search using TF-IDF
            keyword_results = await self._keyword_search(query, limit)
            
            # 3. Combine and re-rank results
            combined_results = await self._combine_and_rerank(
                query, semantic_results, keyword_results, limit
            )
            
            return combined_results
            
        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            # Fallback to semantic search only
            return await self.vector_db.search_knowledge(
                query=query, embedding=embedding, limit=limit, threshold=threshold
            )
    
    async def _keyword_search(self, query: str, limit: int) -> List[KnowledgeSearchResult]:
        """Keyword-based search using TF-IDF similarity"""
        try:
            if not self._is_initialized:
                return []
            
            # Get all documents
            documents = await self.vector_db.get_all_documents()
            if not documents:
                return []
            
            # Calculate TF-IDF similarity
            query_vec = self.tfidf_vectorizer.transform([query])
            doc_vecs = self.tfidf_vectorizer.transform([doc.content for doc in documents])
            
            similarities = cosine_similarity(query_vec, doc_vecs).flatten()
            
            # Get top results
            top_indices = np.argsort(similarities)[::-1][:limit]
            
            results = []
            for idx in top_indices:
                if similarities[idx] > 0.1:  # Minimum similarity threshold
                    doc = documents[idx]
                    # Create a mock search result
                    result = KnowledgeSearchResult(
                        chunk_id=doc.document_id,
                        document_id=doc.document_id,
                        content=doc.content,
                        score=float(similarities[idx]),
                        metadata={
                            "filename": doc.filename,
                            "file_type": doc.file_type,
                            "upload_date": doc.upload_date.isoformat(),
                            "search_type": "keyword"
                        }
                    )
                    results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in keyword search: {e}")
            return []
    
    async def _combine_and_rerank(
        self,
        query: str,
        semantic_results: List[KnowledgeSearchResult],
        keyword_results: List[KnowledgeSearchResult],
        limit: int
    ) -> List[KnowledgeSearchResult]:
        """Combine semantic and keyword results with re-ranking"""
        try:
            # Combine results
            all_results = semantic_results + keyword_results
            
            # Remove duplicates based on document_id
            unique_results = {}
            for result in all_results:
                doc_id = result.document_id
                if doc_id not in unique_results:
                    unique_results[doc_id] = result
                else:
                    # Combine scores if duplicate
                    existing = unique_results[doc_id]
                    existing.score = max(existing.score, result.score)
            
            # Re-rank using query relevance
            reranked_results = await self._rerank_by_relevance(
                query, list(unique_results.values())
            )
            
            # Return top results
            return reranked_results[:limit]
            
        except Exception as e:
            logger.error(f"Error in combine and rerank: {e}")
            return semantic_results[:limit]
    
    async def _rerank_by_relevance(
        self,
        query: str,
        results: List[KnowledgeSearchResult]
    ) -> List[KnowledgeSearchResult]:
        """Re-rank results based on query relevance using LLM"""
        try:
            if len(results) <= 1:
                return results
            
            # Prepare re-ranking prompt
            results_text = "\n".join([
                f"{i+1}. {result.content[:200]}..." 
                for i, result in enumerate(results)
            ])
            
            prompt = f"""
            Rank the following knowledge chunks by their relevance to this query: "{query}"
            
            Knowledge chunks:
            {results_text}
            
            Return only the ranking as a comma-separated list of numbers (1-indexed).
            Most relevant first.
            """
            
            # Get ranking from LLM
            ranking_response = await self.openai_service.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=100
            )
            
            # Parse ranking
            try:
                ranking = [int(x.strip()) - 1 for x in ranking_response.split(',')]
                # Validate ranking
                ranking = [r for r in ranking if 0 <= r < len(results)]
                
                # Apply ranking
                reranked = [results[i] for i in ranking]
                
                # Add any missing results at the end
                ranked_ids = set(ranking)
                for i, result in enumerate(results):
                    if i not in ranked_ids:
                        reranked.append(result)
                
                return reranked
                
            except Exception as parse_error:
                logger.warning(f"Failed to parse ranking: {parse_error}")
                return results
                
        except Exception as e:
            logger.error(f"Error in re-ranking: {e}")
            return results
    
    async def contextual_search(
        self,
        query: str,
        conversation_history: List[str],
        embedding: List[float],
        limit: int = 5
    ) -> List[KnowledgeSearchResult]:
        """
        Context-aware search that considers conversation history
        """
        try:
            # Build contextual query
            if conversation_history:
                # Take last 3 messages for context
                recent_context = conversation_history[-3:]
                contextual_query = f"""
                Recent conversation: {' '.join(recent_context)}
                
                Current question: {query}
                """
            else:
                contextual_query = query
            
            # Generate embedding for contextual query
            contextual_embedding = await self.openai_service.generate_embedding(contextual_query)
            
            # Perform hybrid search with contextual query
            return await self.hybrid_search(
                query=contextual_query,
                embedding=contextual_embedding,
                limit=limit
            )
            
        except Exception as e:
            logger.error(f"Error in contextual search: {e}")
            return await self.hybrid_search(query, embedding, limit)
    
    async def query_expansion(
        self,
        query: str
    ) -> List[str]:
        """
        Expand the query with related terms and concepts
        """
        try:
            prompt = f"""
            Expand this search query with related terms and concepts that would help find relevant information:
            
            Original query: "{query}"
            
            Provide 3-5 expanded queries as a comma-separated list.
            Focus on synonyms, related concepts, and alternative phrasings.
            """
            
            response = await self.openai_service.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=150
            )
            
            # Parse expanded queries
            expanded_queries = [q.strip() for q in response.split(',')]
            expanded_queries = [q for q in expanded_queries if q and q != query]
            
            return expanded_queries[:3]  # Return top 3 expanded queries
            
        except Exception as e:
            logger.error(f"Error in query expansion: {e}")
            return []
    
    async def multi_query_search(
        self,
        query: str,
        embedding: List[float],
        limit: int = 5
    ) -> List[KnowledgeSearchResult]:
        """
        Search using multiple query variations
        """
        try:
            # Get expanded queries
            expanded_queries = await self.query_expansion(query)
            
            # Search with original query
            original_results = await self.hybrid_search(query, embedding, limit)
            
            # Search with expanded queries
            all_results = original_results.copy()
            seen_docs = {result.document_id for result in original_results}
            
            for expanded_query in expanded_queries:
                if len(all_results) >= limit * 2:
                    break
                
                # Generate embedding for expanded query
                expanded_embedding = await self.openai_service.generate_embedding(expanded_query)
                
                # Search with expanded query
                expanded_results = await self.hybrid_search(
                    expanded_query, expanded_embedding, limit
                )
                
                # Add new results
                for result in expanded_results:
                    if result.document_id not in seen_docs:
                        all_results.append(result)
                        seen_docs.add(result.document_id)
            
            # Re-rank all results
            reranked = await self._rerank_by_relevance(query, all_results)
            
            return reranked[:limit]
            
        except Exception as e:
            logger.error(f"Error in multi-query search: {e}")
            return await self.hybrid_search(query, embedding, limit)
