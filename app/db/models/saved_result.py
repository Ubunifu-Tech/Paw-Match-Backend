"""
Saved Result Database Model

Model for storing user's saved breed recommendations.

Author: PawMatch Team
Version: 1.0.0
"""

from sqlalchemy import Column, String, DateTime, Integer, Numeric, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.core.database import Base


class SavedResult(Base):
    """
    Saved breed recommendation model.
    
    Stores user's breed match results for later retrieval.
    Includes match score, rank, and all match data.
    
    Attributes:
        id (UUID): Primary key
        session_id (UUID): Reference to session
        breed_name (str): Name of the breed
        match_score (Numeric): Compatibility score (0-100)
        rank (int): Rank in recommendations (1-3)
        match_data (JSONB): Complete match details
        video_url (str): Generated video URL
        images_used (JSONB): Images used for video
        created_at (DateTime): Save timestamp
    """
    __tablename__ = "saved_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    session_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    breed_name = Column(String(255), nullable=False, index=True)
    match_score = Column(Numeric(5, 2), nullable=True)
    rank = Column(Integer, nullable=True)
    match_data = Column(JSONB, nullable=True)
    video_url = Column(Text, nullable=True)
    images_used = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="saved_results")
    
    def __repr__(self):
        return f"<SavedResult(id={self.id}, breed={self.breed_name}, score={self.match_score})>"
