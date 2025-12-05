"""
User Model

Database model for user accounts with authentication and preferences.

Author: PawMatch Team
Version: 1.0.0
"""

from sqlalchemy import Column, String, Boolean, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from datetime import datetime, timedelta
from app.core.database import Base


class User(Base):
    """
    User account model.
    
    Stores user information, authentication, and preferences.
    Supports anonymous users (no email) and registered users.
    
    Attributes:
        id (UUID): Primary key
        email (str): User email (optional for anonymous)
        username (str): Display name
        is_anonymous (bool): Whether user is anonymous
        preferences (JSONB): User preferences and settings
        api_calls_today (int): API call count for rate limiting
        api_calls_reset_at (DateTime): When to reset API call count
        created_at (DateTime): Account creation timestamp
        last_active_at (DateTime): Last activity timestamp
        sessions (relationship): User's conversation sessions
        saved_results (relationship): User's saved breed matches
    """
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=True, unique=True, index=True)
    username = Column(String(100), nullable=True)
    full_name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=True)
    is_anonymous = Column(Boolean, default=True, nullable=False)
    
    # User preferences and memory
    preferences = Column(JSONB, nullable=True, default=dict)
    cross_session_memory = Column(JSONB, nullable=True, default=dict)
    
    # Rate limiting
    api_calls_today = Column(Integer, default=0, nullable=False)
    api_calls_reset_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_active_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    saved_results = relationship("SavedResult", back_populates="user", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")
    api_usage = relationship("APIUsage", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, anonymous={self.is_anonymous})>"
    
    def increment_api_calls(self):
        """Increment API call count for rate limiting."""
        from datetime import timezone
        now = datetime.now(timezone.utc)
        
        # Reset counter if it's a new day
        if not self.api_calls_reset_at or now >= self.api_calls_reset_at:
            self.api_calls_today = 0
            self.api_calls_reset_at = now + timedelta(days=1)
        
        self.api_calls_today += 1
    
    def can_make_api_call(self, daily_limit: int = 20) -> bool:
        """Check if user can make another API call."""
        from datetime import timezone
        now = datetime.now(timezone.utc)
        
        # Reset if needed
        if not self.api_calls_reset_at or now >= self.api_calls_reset_at:
            return True
        
        return self.api_calls_today < daily_limit
    
    def update_memory(self, key: str, value: any):
        """Update cross-session memory."""
        if self.cross_session_memory is None:
            self.cross_session_memory = {}
        self.cross_session_memory[key] = value
    
    def get_memory(self, key: str, default=None):
        """Get value from cross-session memory."""
        if self.cross_session_memory is None:
            return default
        return self.cross_session_memory.get(key, default)
