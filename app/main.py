"""
PawMatch API - Main Application

AI-powered dog breed recommendation system that helps users find their perfect canine companion.
PawMatch uses conversational AI to match users with compatible dog breeds based on their
lifestyle, preferences, and living situation.

Features:
    - Conversational AI with natural language understanding
    - Sophisticated breed matching algorithm (195 breeds, 17 traits)
    - Personalized content generation (narratives, tips, videos)
    - User accounts with session persistence
    - Rate limiting and usage tracking
    - Web search integration for trusted insights
    - Image service with comprehensive breed gallery

API Documentation:
    - Swagger UI: /docs
    - ReDoc: /redoc
    - Health Check: /health

Author: PawMatch Team
Version: 1.0.0
License: MIT
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.api import chat, recommendations, breeds, users, favorites, video_queue
from app.routes import research
from app.core.config import get_settings
from app.middleware.error_handler import (
    validation_exception_handler,
    http_exception_handler,
    general_exception_handler
)

settings = get_settings()

app = FastAPI(
    title=settings.app_name, 
    version=settings.api_version,
    description="Find your perfect paw-tner! AI-powered dog breed matching using Google Gemini 2.0",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "Richard Pallangyo",
        "email": "rapaugustino@gmail.com",
    },
    license_info={
        "name": "MIT",
    }
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(recommendations.router, prefix="/api")
app.include_router(breeds.router, prefix="/api")
app.include_router(favorites.router, prefix="/api")
app.include_router(research.router, prefix="/api")
app.include_router(video_queue.router, prefix="/api")

# Add exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint providing API information.
    
    Returns basic information about the API including version,
    documentation links, and health check endpoint.
    
    Returns:
        dict: API metadata including version and documentation URLs
    """
    return {
        "message": "PawMatch API - Find Your Perfect Paw-tner! 🐾", 
        "version": settings.api_version,
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", tags=["Health"])
async def health():
    """
    Health check endpoint for monitoring and load balancers.
    
    Returns the current health status and API version. Used by
    monitoring systems, load balancers, and deployment pipelines
    to verify the service is operational.
    
    Returns:
        dict: Health status and version information
        
    Example:
        >>> response = requests.get("http://localhost:8000/health")
        >>> print(response.json())
        {"status": "healthy", "version": "v1"}
    """
    return {"status": "healthy", "version": settings.api_version}