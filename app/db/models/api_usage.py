"""
API Usage Tracking Model

Tracks external API calls (Gemini, etc.) per user for rate limiting and billing.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class APIUsage(Base):
    """Track API usage per user for rate limiting"""
    
    __tablename__ = "api_usage"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    api_type = Column(String, nullable=False, index=True)  # 'research', 'chat', 'video', etc.
    endpoint = Column(String, nullable=False)  # Specific endpoint called
    month = Column(String, nullable=False, index=True)  # 'YYYY-MM' format for monthly limits
    count = Column(Integer, default=1, nullable=False)
    last_used = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship
    user = relationship("User", back_populates="api_usage")
    
    # Composite index for efficient lookups
    __table_args__ = (
        Index('idx_user_api_month', 'user_id', 'api_type', 'month'),
    )
    
    def __repr__(self):
        return f"<APIUsage user_id={self.user_id} api_type={self.api_type} month={self.month} count={self.count}>"
