"""
User Service

Manages user accounts, authentication, preferences, and rate limiting.

Author: PawMatch Team
Version: 1.0.0
"""

from typing import Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import User
from app.core.database import AsyncSessionLocal
import uuid


class UserService:
    """
    User management service.
    
    Handles user creation, authentication, preferences, rate limiting,
    and cross-session memory.
    
    Example:
        >>> service = UserService()
        >>> user = await service.create_anonymous_user()
        >>> can_call = await service.check_rate_limit(user.id, "chat")
    """
    
    async def create_anonymous_user(self) -> User:
        """
        Create an anonymous user.
        
        Anonymous users don't require email and are identified by UUID only.
        They have lower rate limits than registered users.
        
        Returns:
            User: Created anonymous user
        """
        async with AsyncSessionLocal() as db:
            user = User(
                id=uuid.uuid4(),
                is_anonymous=True,
                preferences={},
                cross_session_memory={}
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            return user
    
    async def register_user(self, email: str, username: Optional[str] = None, hashed_password: str = None, full_name: Optional[str] = None) -> Optional[User]:
        """
        Register a user with email.
        
        Converts anonymous user to registered or creates new registered user.
        
        Args:
            email (str): User email
            username (str): Display name (optional)
            hashed_password (str): Hashed password
            full_name (str): User's full name (optional)
            
        Returns:
            Optional[User]: Registered user or None if email exists
        """
        async with AsyncSessionLocal() as db:
            # Check if email already exists
            result = await db.execute(
                select(User).where(User.email == email)
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                return None  # Email already registered
            
            user = User(
                id=uuid.uuid4(),
                email=email,
                username=username or email.split('@')[0],
                full_name=full_name,
                hashed_password=hashed_password,
                is_anonymous=False,
                preferences={},
                cross_session_memory={}
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            return user
    
    async def upgrade_anonymous_to_registered(
        self, 
        user_id: uuid.UUID, 
        email: str, 
        username: Optional[str] = None,
        hashed_password: str = None
    ) -> Optional[User]:
        """
        Upgrade anonymous user to registered.
        
        Args:
            user_id (UUID): Anonymous user ID
            email (str): Email to register
            username (str): Display name (optional)
            hashed_password (str): Hashed password
            
        Returns:
            Optional[User]: Upgraded user or None if email exists
        """
        async with AsyncSessionLocal() as db:
            # Check if email already exists
            result = await db.execute(
                select(User).where(User.email == email)
            )
            if result.scalar_one_or_none():
                return None
            
            # Get anonymous user
            result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user or not user.is_anonymous:
                return None
            
            # Upgrade
            user.email = email
            user.username = username or email.split('@')[0]
            user.hashed_password = hashed_password
            user.is_anonymous = False
            
            await db.commit()
            await db.refresh(user)
            return user
    
    async def get_user(self, user_id: uuid.UUID) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id (UUID): User ID
            
        Returns:
            Optional[User]: User or None
        """
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(User).where(User.id == user_id)
            )
            return result.scalar_one_or_none()
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email.
        
        Args:
            email (str): User email
            
        Returns:
            Optional[User]: User or None
        """
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(User).where(User.email == email)
            )
            return result.scalar_one_or_none()
    
    async def update_preferences(
        self, 
        user_id: uuid.UUID, 
        preferences: Dict[str, Any]
    ) -> Optional[User]:
        """
        Update user preferences.
        
        Args:
            user_id (UUID): User ID
            preferences (dict): Preferences to update
            
        Returns:
            Optional[User]: Updated user or None
        """
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                return None
            
            if user.preferences is None:
                user.preferences = {}
            
            user.preferences.update(preferences)
            # Mark as modified for SQLAlchemy
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(user, "preferences")
            await db.commit()
            await db.refresh(user)
            return user
    
    async def update_memory(
        self, 
        user_id: uuid.UUID, 
        key: str, 
        value: Any
    ) -> Optional[User]:
        """
        Update cross-session memory.
        
        Args:
            user_id (UUID): User ID
            key (str): Memory key
            value (Any): Value to store
            
        Returns:
            Optional[User]: Updated user or None
        """
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                return None
            
            user.update_memory(key, value)
            # Mark as modified for SQLAlchemy
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(user, "cross_session_memory")
            await db.commit()
            await db.refresh(user)
            return user
    
    async def get_memory(
        self, 
        user_id: uuid.UUID, 
        key: str, 
        default: Any = None
    ) -> Any:
        """
        Get value from cross-session memory.
        
        Args:
            user_id (UUID): User ID
            key (str): Memory key
            default (Any): Default value if not found
            
        Returns:
            Any: Stored value or default
        """
        user = await self.get_user(user_id)
        if not user:
            return default
        return user.get_memory(key, default)
    
    async def check_rate_limit(
        self, 
        user_id: uuid.UUID, 
        action: str = "chat"
    ) -> tuple[bool, Optional[str]]:
        """
        Check if user can make an API call.
        
        Args:
            user_id (UUID): User ID
            action (str): Action type (chat, recommendation, etc.)
            
        Returns:
            tuple[bool, Optional[str]]: (can_proceed, error_message)
        """
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                return False, "User not found"
            
            # Define limits based on user type
            if user.is_anonymous:
                daily_limit = 50  # Anonymous users: 50 calls/day
            else:
                daily_limit = 200  # Registered users: 200 calls/day
            
            # Check limit
            if not user.can_make_api_call(daily_limit):
                return False, f"Daily limit exceeded ({daily_limit} calls/day). Please try again tomorrow."
            
            # Increment counter
            user.increment_api_calls()
            await db.commit()
            
            return True, None
    
    async def get_api_usage(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """
        Get user's API usage statistics.
        
        Args:
            user_id (UUID): User ID
            
        Returns:
            dict: Usage statistics
        """
        user = await self.get_user(user_id)
        if not user:
            return {}
        
        daily_limit = 50 if user.is_anonymous else 200
        
        return {
            "calls_today": user.api_calls_today,
            "daily_limit": daily_limit,
            "remaining": max(0, daily_limit - user.api_calls_today),
            "reset_at": user.api_calls_reset_at.isoformat() if user.api_calls_reset_at else None,
            "user_type": "anonymous" if user.is_anonymous else "registered"
        }
    
    async def delete_user_data(self, user_id: uuid.UUID) -> bool:
        """
        Delete all user data (GDPR compliance).
        
        Deletes:
        - User account
        - All sessions (CASCADE)
        - All chat messages (CASCADE)
        - All saved results (CASCADE)
        
        Args:
            user_id (UUID): User ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                return False
            
            await db.delete(user)
            await db.commit()
            return True
