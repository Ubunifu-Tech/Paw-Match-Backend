"""
Conversation Agent Module

This module manages conversational sessions for the dog breed matchmaker chatbot.
It handles user interactions, extracts preferences from natural language, and 
determines when enough information has been gathered to make breed recommendations.

Classes:
    ConversationAgent: Main agent for managing chat sessions and user profiles

Author: PawMatch Team
Version: 1.0.0
"""

from typing import Dict, Any, List, Optional
from app.services.gemini_service import GeminiService
from app.models.user_profile import UserProfile
from app.core.database import AsyncSessionLocal
from app.services.quick_reply_generator import QuickReplyGenerator
from app.db.models import Session, User
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from sqlalchemy import select


class ConversationAgent:
    """
    Manages conversational sessions and user profile extraction.
    
    This agent orchestrates the conversation flow between users and the AI,
    extracting user preferences through natural language processing and
    determining when sufficient information has been gathered for breed matching.
    
    Attributes:
        gemini (GeminiService): Service for AI-powered natural language processing
        
    Example:
        >>> agent = ConversationAgent(gemini_service)
        >>> session_id = await agent.create_session(user_id)
        >>> response = await agent.process_message(session_id, "I want a family dog")
        >>> print(response['message'])
    """
    
    def __init__(self, gemini_service: GeminiService):
        """
        Initialize the conversation agent.
        
        Args:
            gemini_service (GeminiService): Configured Gemini service instance
        """
        self.gemini = gemini_service
    
    async def create_session(self, user_id: uuid.UUID) -> str:
        """
        Create a new conversation session with empty state.
        
        Generates a unique session ID and initializes session storage with
        empty conversation history, user profile, and completion status.
        
        Args:
            user_id (uuid.UUID): The ID of the user creating the session.
            
        Returns:
            str: Unique session identifier (UUID4)
            
        Example:
            >>> session_id = await agent.create_session(user_id)
            >>> print(session_id)
            'a1b2c3d4-e5f6-7890-abcd-ef1234567890'
        """
        async with AsyncSessionLocal() as db:
            session = Session(
                id=uuid.uuid4(),
                user_id=user_id,
                session_data={
                    'history': [],
                    'profile': {},
                    'is_complete': False
                }
            )
            db.add(session)
            await db.commit()
            return str(session.id)
    
    async def get_or_create_session(self, session_id: Optional[str], user_id: uuid.UUID) -> str:
        """
        Retrieve existing session or create a new one if not found.
        
        Args:
            session_id (Optional[str]): Session ID to retrieve, or None to create new
            user_id (uuid.UUID): The ID of the user.
            
        Returns:
            str: Valid session ID (existing or newly created)
            
        Example:
            >>> session_id = await agent.get_or_create_session(None, user_id)  # Creates new
            >>> same_id = await agent.get_or_create_session(session_id, user_id)  # Returns existing
        """
        if session_id:
            try:
                async with AsyncSessionLocal() as db:
                    result = await db.execute(select(Session).where(Session.id == uuid.UUID(session_id)))
                    session = result.scalar_one_or_none()
                    if session and session.user_id == user_id:
                        return session_id
            except (ValueError, AttributeError):
                # Invalid UUID format, create new session
                pass
        return await self.create_session(user_id)

    async def get_session(self, session_id: str) -> Optional[Session]:
        """
        Retrieve a session from the database.
        
        Args:
            session_id (str): The ID of the session to retrieve.
            
        Returns:
            Optional[Session]: The session object, or None if not found.
        """
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Session).where(Session.id == uuid.UUID(session_id)))
            return result.scalar_one_or_none()

    
    async def process_message(
        self, 
        session_id: str, 
        user_message: str
    ) -> Dict[str, Any]:
        """
        Process user message and generate appropriate AI response.
        
        This is the main entry point for conversation handling. It:
        1. Validates/creates session
        2. Detects exit intents
        3. Extracts user preferences from natural language
        4. Determines if enough information is gathered
        5. Generates contextual follow-up questions or completion message
        
        Args:
            session_id (str): Unique session identifier
            user_message (str): User's natural language input
            
        Returns:
            Dict[str, Any]: Response containing:
                - message (str): AI's response text
                - session_id (str): Session identifier
                - is_complete (bool): Whether profile is complete
                - user_profile (dict): Extracted user preferences
                
        Example:
            >>> response = await agent.process_message(
            ...     session_id="abc123",
            ...     user_message="I want a family-friendly dog"
            ... )
            >>> print(response['message'])
            "Great! Do you have children at home?"
        """
        
        async with AsyncSessionLocal() as db:
            # Get session within this db context
            result = await db.execute(select(Session).where(Session.id == uuid.UUID(session_id)))
            session = result.scalar_one_or_none()
            
            if not session:
                # This should not happen if get_or_create_session is used correctly
                raise ValueError("Session not found")

            session_data = session.session_data
            
            # Check if user wants to exit
            exit_phrases = ["no thanks", "stop", "quit", "exit", "cancel", "changed my mind", "don't want", "never mind"]
            if any(phrase in user_message.lower() for phrase in exit_phrases):
                from sqlalchemy.orm.attributes import flag_modified
                response_text = "I understand! No problem at all. If you ever decide to revisit getting a dog, I'm here to help. Take care! 🐕"
                session_data['history'].append({'role': 'user', 'content': user_message})
                session_data['history'].append({'role': 'assistant', 'content': response_text})
                session.session_data = session_data
                flag_modified(session, 'session_data')
                db.add(session)
                await db.commit()
                return {
                    'message': response_text,
                    'session_id': session_id,
                    'is_complete': False,
                    'user_profile': session_data['profile'],
                    'suggested_actions': None  # Don't show quick replies when exiting
                }
            
            # Add user message to history
            session_data['history'].append({'role': 'user', 'content': user_message})
            
            # Extract preferences from conversation
            updated_profile = self.gemini.extract_user_preferences(session_data['history'])
            print(f"Current profile before update: {session_data['profile']}")
            print(f"Extracted updates: {updated_profile}")
            
            # Only update fields that have non-None values to preserve existing data
            for key, value in updated_profile.items():
                if value is not None:
                    session_data['profile'][key] = value
            
            print(f"Profile after update: {session_data['profile']}")
            
            # Mark session_data as modified so SQLAlchemy saves it
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(session, 'session_data')
            
            # Check if we have enough information
            is_complete = self.gemini.should_make_recommendation(
                session_data['history'],
                session_data['profile']
            )
            
            if is_complete:
                response_text = "Great! I have enough information to find your perfect matches. Let me analyze the best breeds for you... 🐕✨"
                session_data['is_complete'] = True
            else:
                # Generate conversational response
                response_text = self.gemini.generate_conversational_response(
                    user_message,
                    session_data['history'],
                    session_data['profile']
                )
            
            # Add assistant response to history
            session_data['history'].append({'role': 'assistant', 'content': response_text})
            
            session.session_data = session_data
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(session, 'session_data')
            db.add(session)
            await db.commit()
            
            # Generate context-aware quick replies
            suggested_actions = QuickReplyGenerator.generate_from_profile_gaps(
                session_data['profile'],
                response_text
            )
            
            return {
                'message': response_text,
                'session_id': session_id,
                'is_complete': is_complete,
                'user_profile': session_data['profile'],
                'suggested_actions': suggested_actions
            }
    
    async def get_user_profile(self, session_id: str) -> Optional[UserProfile]:
        """
        Retrieve validated user profile from session.
        
        Fetches the user profile data from the session and converts it
        to a validated UserProfile model instance.
        
        Args:
            session_id (str): Session identifier
            
        Returns:
            Optional[UserProfile]: Validated user profile or None if session not found
            
        Example:
            >>> profile = await agent.get_user_profile("abc123")
            >>> if profile:
            ...     print(f"Living space: {profile.living_space}")
        """
        session = await self.get_session(session_id)
        if not session:
            return None
        
        profile_data = session.session_data.get('profile', {})
        try:
            return UserProfile(**profile_data)
        except Exception as e:
            print(f"Error creating UserProfile: {e}")
            return None