from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./data/golf_tournament.db"
    
    # Security
    secret_key: str = "your-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Application
    app_name: str = "Abhimata Golf Tournament System"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # CORS - Allow all origins for development
    cors_origins: List[str] = ["*"]
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/golf_tournament.log"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Create settings instance
settings = Settings()

# Ensure data and logs directories exist
os.makedirs("data", exist_ok=True)
os.makedirs("logs", exist_ok=True)
