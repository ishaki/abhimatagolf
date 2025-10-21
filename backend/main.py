from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from core.config import settings
from core.database import create_db_and_tables, get_session
from core.app_logging import logger
from api import auth, users, courses, events, participants, scorecards, event_divisions, leaderboards, excel
from services.live_scoring_service import LiveScoringService
import socketio
import logging


# Global WebSocket service instance
live_scoring_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Abhimata Golf Tournament System")
    create_db_and_tables()
    logger.info("Database tables created")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Abhimata Golf Tournament System")
    # Ensure all logging handlers flush/close to avoid Windows file lock on rotation
    logging.shutdown()

# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="A web-based tournament scoring application for golf event organizers",
    lifespan=lifespan
)

# Initialize WebSocket service after app creation
session = next(get_session())
live_scoring_service = LiveScoringService(session)
logger.info("WebSocket service initialized")

# Create SocketIO app and mount it
sio_app = socketio.ASGIApp(live_scoring_service.get_app(), app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(courses.router)
app.include_router(events.router)
app.include_router(participants.router)
app.include_router(scorecards.router)
app.include_router(event_divisions.router)
app.include_router(leaderboards.router)
app.include_router(excel.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Abhimata Golf Tournament System",
        "version": settings.app_version,
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "version": settings.app_version
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
