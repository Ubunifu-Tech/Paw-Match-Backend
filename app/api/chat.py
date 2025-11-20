"""
Chat API Endpoints

This module provides REST API endpoints for conversational interactions
with the dog breed matchmaker chatbot. Handles message processing,
session management, and user profile extraction.

Endpoints:
    POST /api/chat/message - Send message and receive AI response
    GET /api/chat/session/{session_id} - Retrieve session information

Author: PawMatch Team
Version: 1.0.0
"""

from fastapi import APIRouter, Depends, HTTPException
from app.models.chat import ChatRequest, ChatResponse
from app.services.conversation_agent import ConversationAgent
from app.core.dependencies import get_conversation_agent
from app.core.security import get_current_user
from app.db.models import User

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/message", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    agent: ConversationAgent = Depends(get_conversation_agent),
    current_user: User = Depends(get_current_user)
):
    """
    Send a chat message and receive AI-generated response.
    
    This endpoint processes user messages through the conversational AI,
    extracts preferences, and determines when enough information has been
    gathered to make breed recommendations.
    
    Args:
        request (ChatRequest): Contains message text and optional session_id
        agent (ConversationAgent): Injected conversation agent service
        current_user_id (str): The ID of the current user.
        
    Returns:
        ChatResponse: AI response with updated profile and completion status
        
    Example:
        ```json
        POST /api/chat/message
        {
            "session_id": "abc123",
            "message": "I want a family-friendly dog"
        }
        
        Response:
        {
            "message": "Great! Do you have children at home?",
            "session_id": "abc123",
            "is_complete": false,
            "user_profile": {"has_children": true, ...}
        }
        ```
    """
    
    session_id = await agent.get_or_create_session(request.session_id, current_user.id)
    result = await agent.process_message(session_id, request.message)
    
    return ChatResponse(**result)


@router.get("/session/{session_id}")
async def get_session(
    session_id: str,
    agent: ConversationAgent = Depends(get_conversation_agent),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve session information including conversation history and profile.
    
    Returns the complete session state including all messages exchanged,
    extracted user profile, and completion status. Useful for resuming
    conversations or debugging.
    
    Args:
        session_id (str): Unique session identifier
        agent (ConversationAgent): Injected conversation agent service
        current_user_id (str): The ID of the current user.
        
    Returns:
        dict: Session data including history, profile, and completion status
        
    Raises:
        HTTPException: 404 if session not found
        HTTPException: 403 if user is not authorized to access the session
        
    Example:
        ```
        GET /api/chat/session/abc123
        
        Response:
        {
            "history": [
                {"role": "user", "content": "I want a dog"},
                {"role": "assistant", "content": "Great! ..."}
            ],
            "profile": {"has_children": true, ...},
            "is_complete": false
        }
        ```
    """
    session = await agent.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this session")
    
    return session.session_data