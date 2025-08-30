from pydantic_settings import BaseSettings
from typing import Optional, List
import os


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Project Portfolio Management System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    # Database
    DATABASE_URL: str = "postgresql+psycopg://ppm_user:ppm_pass@localhost:5432/ppm"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Chroma Vector Database
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001
    
    # Ollama
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    AI_MODEL_NAME: str = "gpt-oss:20b"
    OLLAMA_REASONER_MODEL: str = "gpt-oss:20b"
    OLLAMA_EMBED_MODEL: str = "nomic-embed-text:v1.5"
    
    # xLAM Model
    XLAM_MODEL_ID: str = "Salesforce/Llama-xLAM-2-8b-fc-r"
    
    # JWT
    JWT_SECRET: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # Security
    SECRET_KEY: str = "change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # Tenant
    TENANT_DEFAULT: str = "demo"
    
    # File Storage
    FILE_STORAGE_ROOT: str = "./storage"
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".doc", ".docx", ".txt", ".md", ".json", ".csv"]
    
    # Timezone
    TIMEZONE: str = "Asia/Kolkata"
    
    # RAG Settings
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    MAX_RETRIEVAL_RESULTS: int = 10
    
    # AI Settings
    MAX_TOKENS: int = 4000
    TEMPERATURE: float = 0.7
    
    # AI-First Mode Settings
    AI_FIRST_MODE: bool = True
    AI_AUTOPUBLISH_DEFAULT: bool = False
    ENABLE_OCR: bool = True
    AI_GUARDRAILS_ENABLED: bool = True
    AI_CONTINUOUS_LEARNING: bool = True
    
    # AI Guardrails
    AI_MAX_PROJECT_DURATION_DAYS: int = 365 * 2  # 2 years max
    AI_MAX_TASK_DURATION_DAYS: int = 90  # 3 months max
    AI_MAX_WORKLOAD_PERCENT: int = 120  # 120% max workload
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()

# Ensure storage directory exists
os.makedirs(settings.FILE_STORAGE_ROOT, exist_ok=True)
