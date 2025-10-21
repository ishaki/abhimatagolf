import logging
from logging.handlers import RotatingFileHandler
from core.config import settings
import os


def setup_logging():
    """Configure logging for the application"""
    
    # Create logs directory if it doesn't exist
    os.makedirs(os.path.dirname(settings.log_file), exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            RotatingFileHandler(
                settings.log_file,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5,
                delay=True
            ),
            logging.StreamHandler()
        ]
    )
    
    # Create logger for this module
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured - Level: {settings.log_level}, File: {settings.log_file}")
    
    return logger


# Initialize logging
logger = setup_logging()
