from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import neo4j_conn

logger = structlog.get_logger(__name__)

# Lifespan handler to manage startup and shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Topic-to-Course API...")
    # Connect to Neo4j
    await neo4j_conn.connect_async()
    await neo4j_conn.verify_connection()
    
    logger.info(f"{settings.PROJECT_NAME} API started successfully")
    yield
    # Shutdown
    logger.info("Shutting down API...")
    await neo4j_conn.close()
    logger.info("API shutdown complete")


# Create FastAPI app with lifespan
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="AI-powered course generator using real books and thoughtful assignments",
    lifespan=lifespan
)

# CORS Middleware - Important for your Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],   # Vite default dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "debug": settings.DEBUG
    }

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to Topic-to-Course API",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,           # Auto-reload during development
        log_level="info"
    )