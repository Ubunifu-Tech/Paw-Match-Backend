"""
Breed Data Database Models

Models for storing breed information and images in PostgreSQL.

Author: PawMatch Team
Version: 1.0.0
"""

from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import DateTime
import uuid
from app.core.database import Base


class Breed(Base):
    """
    Dog breed information model.
    
    Stores breed details and traits for quick database access.
    
    Attributes:
        id (UUID): Primary key
        name (str): Breed name
        traits (JSONB): All breed traits (17 traits)
        description (str): Breed description
        created_at (DateTime): Record creation timestamp
        images (relationship): Related breed images
    """
    __tablename__ = "breeds"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True, index=True)
    traits = Column(JSONB, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    images = relationship("BreedImage", back_populates="breed", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Breed(name={self.name})>"


class BreedImage(Base):
    """
    Breed image URLs model.
    
    Stores image URLs for each breed from the GitHub dataset.
    
    Attributes:
        id (UUID): Primary key
        breed_id (UUID): Foreign key to breed
        url (str): Image URL
        image_number (int): Image number (1-35)
        breed_folder (str): Folder name in dataset
        created_at (DateTime): Record creation timestamp
        breed (relationship): Parent breed
    """
    __tablename__ = "breed_images"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    breed_id = Column(UUID(as_uuid=True), ForeignKey("breeds.id", ondelete="CASCADE"), nullable=False, index=True)
    url = Column(Text, nullable=False)
    image_number = Column(Integer, nullable=False)
    breed_folder = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    breed = relationship("Breed", back_populates="images")
    
    def __repr__(self):
        return f"<BreedImage(breed_id={self.breed_id}, number={self.image_number})>"
