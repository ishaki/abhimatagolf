"""
Database initialization and migration utilities
"""
from sqlmodel import SQLModel, create_engine
from core.database import engine
from core.config import settings
import logging

logger = logging.getLogger(__name__)


def init_db() -> None:
    """Initialize database tables"""
    try:
        SQLModel.metadata.create_all(engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


def reset_db() -> None:
    """Reset database by dropping and recreating all tables"""
    try:
        SQLModel.metadata.drop_all(engine)
        SQLModel.metadata.create_all(engine)
        logger.info("Database reset successfully")
    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        raise


def check_db_connection() -> bool:
    """Check if database connection is working"""
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


if __name__ == "__main__":
    # Initialize database when run directly
    init_db()
    print("Database initialized successfully")
