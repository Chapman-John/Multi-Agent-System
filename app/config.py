from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Configuration
    APP_NAME: str = "Multi-Agent AI System"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # API Keys
    OPENAI_API_KEY: str
    ANTHROPIC_API_KEY: str
    TAVILY_API_KEY: Optional[str] = None
    
    # Database
    REDIS_URL: str = "redis://localhost:6379"
    VECTOR_DB_PATH: str = "./storage/vector_db"
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    class Config:
        env_file = ".env"

settings = Settings()