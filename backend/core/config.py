from pydantic_settings import BaseSettings
from typing import List, Optional
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

    # Logging Security Features
    # Enable log encryption for sensitive logs (audit, security)
    log_encryption_enabled: bool = False
    log_encryption_key: Optional[str] = None  # Base64 Fernet key from env
    log_encryption_password: Optional[str] = None  # Alternative: derive key from password
    log_encryption_salt: str = "abhimata-golf-logs-2024"
    encrypted_log_types: List[str] = ["audit", "security"]

    # Enable HMAC tamper detection for audit logs
    log_tamper_detection_enabled: bool = True
    log_hmac_secret: str = "change-this-hmac-secret-in-production"
    signed_log_types: List[str] = ["audit", "security"]

    # Log retention and archival (days)
    log_retention_days_app: int = 30
    log_retention_days_audit: int = 365
    log_retention_days_security: int = 365
    log_retention_days_performance: int = 7
    log_retention_days_error: int = 90
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Create settings instance
settings = Settings()

# Ensure data and logs directories exist
os.makedirs("data", exist_ok=True)
os.makedirs("logs", exist_ok=True)
