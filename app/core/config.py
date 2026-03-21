from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # OpenAI Configuration
    openai_api_key: str
    openai_model: str = "gpt-4"
    openai_embedding_model: str = "text-embedding-3-small"
    
    # Qdrant Configuration
    qdrant_host: str = "localhost"
    qdrant_port: int = 6334
    qdrant_collection_name: str = "personal_knowledge"
    
    # Application Configuration
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = True
    
    # File Upload Configuration
    max_file_size: int = 52428800  # 50MB in bytes
    allowed_extensions_str: str = "pdf,txt,docx,jpg,jpeg,png,wav,mp3,m4a,md"
    upload_dir: str = "uploads"
    data_dir: str = "data"
    
    # Knowledge Processing
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_knowledge_results: int = 5
    
    # Session Configuration
    session_timeout: int = 3600  # 1 hour
    max_conversation_length: int = 20
    
    @property
    def allowed_extensions(self) -> List[str]:
        return [ext.strip() for ext in self.allowed_extensions_str.split(',')]
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Allow extra fields in env

# Create global settings instance
settings = Settings()

# Ensure directories exist
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(settings.data_dir, exist_ok=True)
