from typing import Optional

from app.core.config import settings
from app.services.elasticsearch_service import ElasticsearchService
from app.services.qdrant_service import QdrantService

_vector_db_instance: Optional[object] = None
_vector_db_type: Optional[str] = None


def get_vector_db():
    """
    Return a singleton instance of the selected vector DB backend.

    Keep Qdrant available for rollback/future multi-search.
    """
    global _vector_db_instance, _vector_db_type

    vector_db_type = (settings.vector_db or "qdrant").lower()
    if _vector_db_instance is not None and _vector_db_type == vector_db_type:
        return _vector_db_instance

    if vector_db_type == "elasticsearch":
        _vector_db_instance = ElasticsearchService()
    elif vector_db_type == "qdrant":
        _vector_db_instance = QdrantService()
    else:
        raise ValueError(f"Unsupported vector_db: {vector_db_type}")

    _vector_db_type = vector_db_type
    return _vector_db_instance

