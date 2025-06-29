import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost/qchatbot"
    
    # Azure OpenAI
    AZURE_OPENAI_API_KEY: Optional[str] = None
    AZURE_OPENAI_ENDPOINT: Optional[str] = None
    AZURE_OPENAI_API_VERSION: str = "2023-05-15"
    
    # OpenAI (fallback)
    OPENAI_API_KEY: Optional[str] = None
    
    # Cohere
    COHERE_API_KEY: Optional[str] = None
    
    # HuggingFace
    HUGGINGFACE_API_KEY: Optional[str] = None
    
    # Default embedding model
    DEFAULT_EMBEDDING_MODEL: str = "text-embedding-ada-002"
    
    # Vector dimensions for different models
    EMBEDDING_DIMENSIONS = {
        "text-embedding-ada-002": 1536,
        "BAAI/bge-large-en-v1.5": 1024,
        "BAAI/bge-base-en-v1.5": 768,
        "intfloat/e5-large-v2": 1024,
        "intfloat/e5-base-v2": 768,
        "sentence-transformers/all-MiniLM-L6-v2": 384,
        "cohere-embed-v3": 1024
    }
    
    # File upload settings
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: list = [".pdf", ".docx"]
    
    # Vector search settings
    TOP_K_RESULTS: int = 5
    SIMILARITY_THRESHOLD: float = 0.7
    
    class Config:
        env_file = ".env"

settings = Settings() 