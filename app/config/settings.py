from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # App
    APP_NAME: str = "IssueSpotter"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str
    
    # Qdrant Vector Database
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION_NAME: str = "issue_embeddings"
    QDRANT_API_URL: Optional[str] = None  # For cloud Qdrant
    QDRANT_API_KEY: Optional[str] = None  # For cloud Qdrant
    
    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Celery
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    
    # Webhook - Main Backend Integration
    MAIN_BACKEND_WEBHOOK_URL: Optional[str] = None  # e.g., "https://main-backend.com/api/webhook/moderation"
    
    # AI Thresholds (Phase 4)
    AI_THRESHOLD_GREEN: float = 0.3   # Below this = auto-approve
    AI_THRESHOLD_RED: float = 0.8     # Above this = auto-reject
    
    # Video Processing Limits
    MAX_VIDEO_DURATION_SECONDS: int = 60
    MAX_VIDEO_SIZE_MB: int = 50
    VIDEO_FRAME_INTERVAL_SECONDS: int = 2
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"  # Ignore extra env vars not defined in the model
    )

settings = Settings()