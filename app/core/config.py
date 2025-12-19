from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "n8n Workflow Popularity Tracker"
    API_V1_STR: str = "/api/v1"
    ENV: str = "dev"
    
    # Database
    DATABASE_URL: str
    
    # Platform APIs
    YOUTUBE_API_KEY: Optional[str] = None
    DISCOURSE_API_KEY: Optional[str] = None
    
    # Collection Settings
    DAILY_QUOTA_YOUTUBE: int = 10000
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"

settings = Settings()
