"""
Favorite Model

Stores user's favorite breeds.

Author: PawMatch Team
Version: 1.0.0
"""

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base


class Favorite(Base):
    """
    User's favorite breeds.
    
    Attributes:
        id (UUID): Primary key
        user_id (UUID): Foreign key to User
        breed_id (UUID): Foreign key to Breed
        created_at (DateTime): When the favorite was added
    """
    __tablename__ = "favorites"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    breed_id = Column(UUID(as_uuid=True), ForeignKey("breeds.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="favorites")
    breed = relationship("Breed")
    
    def __repr__(self):
        return f"<Favorite(user_id={self.user_id}, breed_id={self.breed_id})>"
