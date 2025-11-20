"""
Session and ChatMessage Database Models

Models for storing conversation sessions and chat messages in PostgreSQL.

Author: PawMatch Team
Version: 1.0.0
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, BigInteger
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.core.database import Base


class Session(Base):
    """
    User conversation session model.
    
    Stores conversation state, user profile, and completion status.
    Sessions can be resumed and are used to track user progress.
    
    Attributes:
        id (UUID): Primary key
        session_data (JSONB): Flexible session data storage
        user_profile (JSONB): Extracted user preferences
        is_complete (bool): Whether profile is complete
        created_at (DateTime): Session creation timestamp
        updated_at (DateTime): Last update timestamp
        expires_at (DateTime): Session expiration timestamp
        messages (relationship): Related chat messages
    """
    __tablename__ = "sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    session_data = Column(JSONB, nullable=False, default=dict)
    user_profile = Column(JSONB, nullable=True)
    is_complete = Column(Boolean, default=False, nullable=False)
    summary = Column(Text, nullable=True)  # For context optimization
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Session(id={self.id}, is_complete={self.is_complete})>"


class ChatMessage(Base):
    """
    Individual chat message model.
    
    Stores messages exchanged between user and AI assistant.
    Linked to a parent session for conversation history.
    
    Attributes:
        id (BigInteger): Primary key
        session_id (UUID): Foreign key to session
        role (str): Message role ('user' or 'assistant')
        content (Text): Message content
        metadata (JSONB): Additional message metadata
        created_at (DateTime): Message timestamp
        session (relationship): Parent session
    """
    __tablename__ = "chat_messages"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    message_metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    session = relationship("Session", back_populates="messages")
    
    def __repr__(self):
        return f"<ChatMessage(id={self.id}, role={self.role}, session_id={self.session_id})>"
