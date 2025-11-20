from functools import lru_cache
from typing import AsyncGenerator
from app.services.breed_service import BreedService
from app.services.matching_engine import MatchingEngine
from app.services.gemini_service import GeminiService
from app.services.conversation_agent import ConversationAgent
from app.services.content_generator import ContentGenerator
from app.services.image_service import ImageService
from app.services.search_service import SearchService
from app.services.cache_service import CacheService
from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from sqlalchemy.ext.asyncio import AsyncSession

def get_breed_service():
    """Get breed service instance (database-backed)"""
    return BreedService()

def get_matching_engine():
    """Get matching engine instance"""
    return MatchingEngine()

@lru_cache()
def get_gemini_service():
    settings = get_settings()
    # Breed context will be loaded async when needed
    # For now, provide minimal context
    breed_context = "PawMatch has 195 dog breeds in the database."
    
    return GeminiService(settings.gemini_api_key, breed_context=breed_context)

@lru_cache()
def get_conversation_agent():
    return ConversationAgent(get_gemini_service())

@lru_cache()
def get_content_generator():
    return ContentGenerator(get_gemini_service())

def get_image_service():
    """Get ImageService instance - no caching to ensure fresh DB connections"""
    return ImageService()

@lru_cache()
def get_search_service():
    return SearchService(get_gemini_service())

@lru_cache()
def get_cache_service():
    return CacheService()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()