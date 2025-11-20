"""
Database Models Package

Contains all SQLAlchemy ORM models for the application.

Models:
    - Session: User conversation sessions
    - ChatMessage: Individual chat messages
    - SavedResult: User's saved breed recommendations
    - Breed: Dog breed information
    - BreedImage: Breed image URLs
    
Author: PawMatch Team
Version: 1.0.0
"""

from app.db.models.user import User
from app.db.models.session import Session, ChatMessage
from app.db.models.saved_result import SavedResult
from app.db.models.breed_data import Breed, BreedImage
from app.db.models.favorite import Favorite

__all__ = ["User", "Session", "ChatMessage", "SavedResult", "Breed", "BreedImage", "Favorite"]
