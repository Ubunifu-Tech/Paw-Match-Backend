"""
Session Service

Manages conversation sessions with database persistence.

Author: PawMatch Team
Version: 1.0.0
"""

from typing import Optional, List, Dict, Any
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Session, ChatMessage, User
from app.core.database import AsyncSessionLocal
from datetime import datetime, timedelta
import uuid


class SessionService:
    """
    Session management service with database persistence.
    
    Handles session creation, loading, saving, and conversation history.
    Supports session resumption and context optimization.
    
    Example:
        >>> service = SessionService()
        >>> session = await service.create_session(user_id)
        >>> await service.save_message(session.id, "user", "Hello")
    """
    
    async def create_session(
        self, 
        user_id: Optional[uuid.UUID] = None,
        expires_in_days: int = 30
    ) -> Session:
        """
        Create a new conversation session.
        
        Args:
            user_id (UUID): User ID (optional for anonymous)
            expires_in_days (int): Days until session expires
            
        Returns:
            Session: Created session
        """
        async with AsyncSessionLocal() as db:
            session = Session(
                id=uuid.uuid4(),
                user_id=user_id,
                session_data={"history": []},
                user_profile={},
                is_complete=False,
                expires_at=datetime.utcnow() + timedelta(days=expires_in_days)
            )
            db.add(session)
            await db.commit()
            await db.refresh(session)
            return session
    
    async def get_session(self, session_id: uuid.UUID) -> Optional[Session]:
        """
        Get session by ID.
        
        Args:
            session_id (UUID): Session ID
            
        Returns:
            Optional[Session]: Session or None
        """
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Session).where(Session.id == session_id)
            )
            return result.scalar_one_or_none()
    
    async def save_message(
        self, 
        session_id: uuid.UUID, 
        role: str, 
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[ChatMessage]:
        """
        Save a chat message to the session.
        
        Args:
            session_id (UUID): Session ID
            role (str): Message role (user/assistant)
            content (str): Message content
            metadata (dict): Optional metadata
            
        Returns:
            Optional[ChatMessage]: Saved message or None
        """
        async with AsyncSessionLocal() as db:
            # Check session exists
            result = await db.execute(
                select(Session).where(Session.id == session_id)
            )
            session = result.scalar_one_or_none()
            
            if not session:
                return None
            
            # Create message
            message = ChatMessage(
                session_id=session_id,
                role=role,
                content=content,
                message_metadata=metadata or {}
            )
            db.add(message)
            
            # Update session data
            if session.session_data is None:
                session.session_data = {"history": []}
            
            if "history" not in session.session_data:
                session.session_data["history"] = []
            
            session.session_data["history"].append({
                "role": role,
                "content": content
            })
            
            await db.commit()
            await db.refresh(message)
            return message
    
    async def get_messages(
        self, 
        session_id: uuid.UUID, 
        limit: Optional[int] = None
    ) -> List[ChatMessage]:
        """
        Get messages for a session.
        
        Args:
            session_id (UUID): Session ID
            limit (int): Maximum messages to return (most recent)
            
        Returns:
            List[ChatMessage]: List of messages
        """
        async with AsyncSessionLocal() as db:
            query = select(ChatMessage).where(
                ChatMessage.session_id == session_id
            ).order_by(ChatMessage.created_at)
            
            if limit:
                query = query.limit(limit)
            
            result = await db.execute(query)
            return list(result.scalars().all())
    
    async def update_profile(
        self, 
        session_id: uuid.UUID, 
        profile: Dict[str, Any]
    ) -> Optional[Session]:
        """
        Update user profile in session.
        
        Args:
            session_id (UUID): Session ID
            profile (dict): User profile data
            
        Returns:
            Optional[Session]: Updated session or None
        """
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Session).where(Session.id == session_id)
            )
            session = result.scalar_one_or_none()
            
            if not session:
                return None
            
            session.user_profile = profile
            await db.commit()
            await db.refresh(session)
            return session
    
    async def mark_complete(self, session_id: uuid.UUID) -> Optional[Session]:
        """
        Mark session as complete (ready for recommendations).
        
        Args:
            session_id (UUID): Session ID
            
        Returns:
            Optional[Session]: Updated session or None
        """
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Session).where(Session.id == session_id)
            )
            session = result.scalar_one_or_none()
            
            if not session:
                return None
            
            session.is_complete = True
            await db.commit()
            await db.refresh(session)
            return session
    
    async def summarize_session(
        self, 
        session_id: uuid.UUID, 
        summary: str
    ) -> Optional[Session]:
        """
        Store conversation summary for context optimization.
        
        Args:
            session_id (UUID): Session ID
            summary (str): Conversation summary
            
        Returns:
            Optional[Session]: Updated session or None
        """
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Session).where(Session.id == session_id)
            )
            session = result.scalar_one_or_none()
            
            if not session:
                return None
            
            session.summary = summary
            await db.commit()
            await db.refresh(session)
            return session
    
    async def get_user_sessions(
        self, 
        user_id: uuid.UUID, 
        limit: int = 10
    ) -> List[Session]:
        """
        Get user's sessions (most recent first).
        
        Args:
            user_id (UUID): User ID
            limit (int): Maximum sessions to return
            
        Returns:
            List[Session]: List of sessions
        """
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Session)
                .where(Session.user_id == user_id)
                .order_by(desc(Session.updated_at))
                .limit(limit)
            )
            return list(result.scalars().all())
    
    async def delete_session(self, session_id: uuid.UUID) -> bool:
        """
        Delete a session and all its messages.
        
        Args:
            session_id (UUID): Session ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Session).where(Session.id == session_id)
            )
            session = result.scalar_one_or_none()
            
            if not session:
                return False
            
            await db.delete(session)
            await db.commit()
            return True
    
    async def get_conversation_history(
        self, 
        session_id: uuid.UUID,
        include_summary: bool = True
    ) -> Dict[str, Any]:
        """
        Get complete conversation history with optional summary.
        
        Args:
            session_id (UUID): Session ID
            include_summary (bool): Include summary if available
            
        Returns:
            dict: Conversation history
        """
        session = await self.get_session(session_id)
        if not session:
            return {}
        
        messages = await self.get_messages(session_id)
        
        history = {
            "session_id": str(session.id),
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.created_at.isoformat()
                }
                for msg in messages
            ],
            "profile": session.user_profile,
            "is_complete": session.is_complete,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat()
        }
        
        if include_summary and session.summary:
            history["summary"] = session.summary
        
        return history
