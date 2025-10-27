from sqlmodel import SQLModel, create_engine, Session
from core.config import settings
import os


# Create database engine
engine = create_engine(
    settings.database_url,
    echo=settings.debug,  # Log SQL queries in debug mode
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)


def create_db_and_tables():
    """Create database tables"""
    # Import all models to ensure they are registered with SQLModel
    # This must be done before create_all() is called
    import models  # This imports all models from models/__init__.py

    SQLModel.metadata.create_all(engine)


def get_session():
    """Get database session"""
    with Session(engine) as session:
        yield session


def init_database():
    """Initialize database with tables and seed data"""
    create_db_and_tables()
    
    # Import and run seed data
    from core.seed_data import create_seed_data
    create_seed_data()
    
    print("Database initialized successfully")
