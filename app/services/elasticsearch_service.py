import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

from app.core.config import settings
from app.models.knowledge import KnowledgeChunk, KnowledgeDocument, KnowledgeSearchResult

logger = logging.getLogger(__name__)


class ElasticsearchService:
    """
    Dense-vector storage/search layer implemented on top of Elasticsearch.

    Important: this service intentionally mirrors the public methods of QdrantService
    so the rest of the codebase can switch between engines safely.
    """

    def __init__(self):
        auth: Optional[Dict[str, Any]] = None
        headers: Optional[Dict[str, str]] = None

        if settings.elasticsearch_api_key:
            headers = {"Authorization": f"ApiKey {settings.elasticsearch_api_key}"}
        elif settings.elasticsearch_username and settings.elasticsearch_password:
            auth = {"basic_auth": (settings.elasticsearch_username, settings.elasticsearch_password)}

        # Use synchronous client to avoid dependency on aiohttp transports.
        self.client = Elasticsearch(
            hosts=[
                {
                    "host": settings.elasticsearch_host,
                    "port": settings.elasticsearch_port,
                    "scheme": settings.elasticsearch_scheme,
                }
            ],
            request_timeout=settings.elasticsearch_request_timeout,
            verify_certs=settings.elasticsearch_verify_certs,
            headers=headers,
            **(auth or {}),
        )
        self.index_name = settings.elasticsearch_index_name

    async def initialize_collection(self):
        """Ensure the vector index exists."""
        return await asyncio.to_thread(self._initialize_collection_sync)

    def _initialize_collection_sync(self) -> None:
        try:
            exists = self.client.indices.exists(index=self.index_name)
            if exists:
                return

            dims = settings.elasticsearch_embedding_dims
            mapping = {
                "mappings": {
                    "dynamic": "false",
                    "properties": {
                        "document_id": {"type": "keyword"},
                        "filename": {"type": "keyword"},
                        "file_type": {"type": "keyword"},
                        "content": {"type": "text"},
                        # Store arbitrary extracted knowledge safely in _source (not indexed).
                        "metadata": {"type": "object", "enabled": False},
                        "created_at": {"type": "date"},
                        "embedding": {
                            "type": "dense_vector",
                            "dims": dims,
                        },
                    },
                }
            }

            self.client.indices.create(index=self.index_name, body=mapping)
            logger.info(f"Created Elasticsearch index: {self.index_name}")
        except Exception as e:
            logger.error(f"Error initializing Elasticsearch index: {e}")
            # Keep running if index exists but race happened.

    async def add_chunks_with_embeddings(self, chunks: List[KnowledgeChunk]):
        """Upsert chunk documents with pre-computed embeddings."""
        return await asyncio.to_thread(self._add_chunks_with_embeddings_sync, chunks)

    def _add_chunks_with_embeddings_sync(self, chunks: List[KnowledgeChunk]) -> None:
        try:
            self._initialize_collection_sync()

            actions = []
            for chunk in chunks:
                if chunk.embedding is None:
                    raise ValueError(f"Chunk {chunk.chunk_id} missing embedding.")

                actions.append(
                    {
                        "_op_type": "index",
                        "_index": self.index_name,
                        "_id": chunk.chunk_id,
                        "_source": {
                            "document_id": chunk.document_id,
                            "filename": chunk.metadata.get("filename") or "unknown",
                            "file_type": chunk.metadata.get("file_type") or "unknown",
                            "content": chunk.content,
                            "metadata": chunk.metadata,
                            "created_at": chunk.created_at.isoformat(),
                            "embedding": chunk.embedding,
                        },
                    }
                )

            # bulk does not support "refresh" in a consistent way across helper versions;
            # we force refresh at the end by refreshing the index.
            bulk(self.client, actions, refresh=True)
            logger.info(f"Upserted {len(chunks)} chunks into Elasticsearch")
        except Exception as e:
            logger.error(f"Error adding chunks to Elasticsearch: {e}")
            raise

    async def search_knowledge(
        self,
        query: str,  # unused (kept for signature parity)
        embedding: List[float],
        limit: int = 5,
        threshold: Optional[float] = None,
    ) -> List[KnowledgeSearchResult]:
        """Semantic search using dense_vector + cosineSimilarity script_score."""
        return await asyncio.to_thread(
            self._search_knowledge_sync,
            query,
            embedding,
            limit,
            threshold,
        )

    def _search_knowledge_sync(
        self,
        query: str,
        embedding: List[float],
        limit: int,
        threshold: Optional[float],
    ) -> List[KnowledgeSearchResult]:
        try:
            self._initialize_collection_sync()

            if threshold is None:
                threshold = settings.elasticsearch_search_threshold

            body = {
                "size": limit,
                "min_score": threshold,
                "query": {
                    "script_score": {
                        "query": {"match_all": {}},
                        "script": {
                            # ES returns cosineSimilarity in [-1..1]. We map it to [0..1]
                            # so our existing thresholds (written for Qdrant) behave similarly.
                            "source": "(cosineSimilarity(params.query_vector, 'embedding') + 1.0) / 2.0",
                            "params": {"query_vector": embedding},
                        },
                    }
                },
            }

            resp = self.client.search(index=self.index_name, body=body)
            hits = resp.get("hits", {}).get("hits", [])

            results: List[KnowledgeSearchResult] = []
            for hit in hits:
                source = hit.get("_source", {}) or {}
                results.append(
                    KnowledgeSearchResult(
                        chunk_id=hit.get("_id", ""),
                        document_id=source.get("document_id", ""),
                        content=source.get("content", ""),
                        score=float(hit.get("_score", 0.0)),
                        metadata=source.get("metadata", {}) or {},
                    )
                )

            return results
        except Exception as e:
            logger.error(f"Error searching knowledge in Elasticsearch: {e}")
            raise

    async def get_all_documents(self) -> List[KnowledgeDocument]:
        """Fetch all chunk docs and reconstruct KnowledgeDocument per document_id."""
        return await asyncio.to_thread(self._get_all_documents_sync)

    def _get_all_documents_sync(self) -> List[KnowledgeDocument]:
        try:
            self._initialize_collection_sync()

            documents: Dict[str, Dict[str, Any]] = {}

            # Scroll to avoid loading everything in a single request.
            page_size = 500
            resp = self.client.search(
                index=self.index_name,
                body={"query": {"match_all": {}}},
                size=page_size,
                scroll="2m",
                _source=[
                    "document_id",
                    "filename",
                    "file_type",
                    "content",
                    "metadata",
                    "created_at",
                ],
            )

            scroll_id = resp.get("_scroll_id")
            hits = resp.get("hits", {}).get("hits", [])

            while hits:
                for hit in hits:
                    source = hit.get("_source", {}) or {}
                    doc_id = source.get("document_id")
                    if not doc_id:
                        continue

                    if doc_id not in documents:
                        created_at_raw = source.get("created_at")
                        created_at_dt = (
                            datetime.fromisoformat(created_at_raw) if created_at_raw else datetime.now()
                        )

                        documents[doc_id] = {
                            "document_id": doc_id,
                            "filename": source.get("filename", "unknown"),
                            "file_type": source.get("file_type", "unknown"),
                            "content": "",
                            "metadata": source.get("metadata", {}) or {},
                            "created_at": created_at_dt,
                            "chunks": [],
                        }

                    documents[doc_id]["chunks"].append(source.get("content", ""))

                if not scroll_id:
                    break

                resp = self.client.scroll(scroll_id=scroll_id, scroll="2m")
                scroll_id = resp.get("_scroll_id")
                hits = resp.get("hits", {}).get("hits", [])

            # Combine chunks per document
            document_list: List[KnowledgeDocument] = []
            for doc_data in documents.values():
                doc_data["content"] = "\n\n".join(doc_data["chunks"])
                doc_data.pop("chunks", None)
                document_list.append(KnowledgeDocument(**doc_data))

            return document_list
        except Exception as e:
            logger.error(f"Error getting documents from Elasticsearch: {e}")
            raise

    async def delete_document(self, document_id: str) -> bool:
        """Delete all chunks for a given document_id."""
        return await asyncio.to_thread(self._delete_document_sync, document_id)

    def _delete_document_sync(self, document_id: str) -> bool:
        try:
            self._initialize_collection_sync()

            query = {"query": {"term": {"document_id": document_id}}}
            resp = self.client.delete_by_query(index=self.index_name, body=query, refresh=True)

            deleted = int(resp.get("deleted", 0) or 0)
            return deleted > 0
        except Exception as e:
            logger.error(f"Error deleting document from Elasticsearch: {e}")
            return False

    async def get_collection_stats(self) -> Dict[str, Any]:
        """Return basic index stats with a Qdrant-like shape."""
        return await asyncio.to_thread(self._get_collection_stats_sync)

    def _get_collection_stats_sync(self) -> Dict[str, Any]:
        try:
            self._initialize_collection_sync()

            index_stats = self.client.indices.stats(index=self.index_name)
            stats_for_index = index_stats.get("indices", {}).get(self.index_name, {})

            total = stats_for_index.get("total", {}) or {}
            docs = total.get("docs", {}) or {}

            # Store sizes: may vary by ES version; best-effort.
            store_size = total.get("store_size_in_bytes")
            if isinstance(store_size, dict):
                store_size_in_bytes = store_size.get("value")
            else:
                store_size_in_bytes = store_size

            return {
                "name": self.index_name,
                "vectors_count": int(docs.get("count", 0) or 0),
                "segments_count": None,
                "disk_data_size": store_size_in_bytes,
                "ram_data_size": None,
                "vector_size": settings.elasticsearch_embedding_dims,
                "distance_metric": "cosine",
            }
        except Exception as e:
            logger.error(f"Error getting Elasticsearch index stats: {e}")
            raise

    def _chunk_text(self, text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
        """Split text into chunks (parity with QdrantService)."""
        if chunk_size is None:
            chunk_size = settings.chunk_size
        if overlap is None:
            overlap = settings.chunk_overlap

        chunks: List[str] = []
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

