"""
User API Endpoints

Provides endpoints for user management, preferences, and data control.

Author: PawMatch Team
Version: 1.0.0
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any, List
from app.services.user_service import UserService
from app.services.session_service import SessionService
from app.core.security import create_access_token, get_current_user, verify_password, get_password_hash, validate_password_strength
from app.db.models import User
import uuid

router = APIRouter(prefix="/users", tags=["users"])

class Token(BaseModel):
    access_token: str
    token_type: str

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token login endpoint.
    
    Authenticates user with email and password, returns JWT access token.
    Includes rate limiting to prevent brute force attacks.
    """
    service = UserService()
    user = await service.get_user_by_email(form_data.username)
    
    # Check rate limit before validating credentials to prevent timing attacks
    if user:
        can_proceed, error_msg = await service.check_rate_limit(user.id, "login")
        if not can_proceed:
            raise HTTPException(
                status_code=429,
                detail="Too many login attempts. Please try again later."
            )
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}



# Request/Response Models
class AnonymousUserResponse(BaseModel):
    user_id: str
    is_anonymous: bool
    api_usage: Dict[str, Any]


class RegisterRequest(BaseModel):
    email: EmailStr
    username: Optional[str] = None
    full_name: Optional[str] = None
    password: str


class UpgradeRequest(BaseModel):
    user_id: str
    email: EmailStr
    username: Optional[str] = None
    password: str


class UserResponse(BaseModel):
    user_id: str
    email: Optional[str]
    username: Optional[str]
    is_anonymous: bool
    preferences: Dict[str, Any]
    cross_session_memory: Dict[str, Any]
    api_usage: Dict[str, Any]
    created_at: str


class UpdatePreferencesRequest(BaseModel):
    preferences: Dict[str, Any]


class SessionSummary(BaseModel):
    session_id: str
    is_complete: bool
    created_at: str
    updated_at: str
    message_count: int


# Endpoints
@router.post("/anonymous", response_model=AnonymousUserResponse)
async def create_anonymous_user():
    """
    Create an anonymous user.
    
    Anonymous users can use the app without registration.
    They have lower rate limits than registered users.
    
    Returns:
        AnonymousUserResponse: Created user with ID and usage info
    """
    service = UserService()
    user = await service.create_anonymous_user()
    usage = await service.get_api_usage(user.id)
    
    return AnonymousUserResponse(
        user_id=str(user.id),
        is_anonymous=user.is_anonymous,
        api_usage=usage
    )


@router.post("/register", response_model=UserResponse)
async def register_user(request: RegisterRequest):
    """
    Register a new user with email.
    
    Registered users get higher rate limits and can save their data.
    
    Args:
        request: Registration details (email, username, password)
        
    Returns:
        UserResponse: Registered user details
        
    Raises:
        HTTPException: 400 if email already exists or password is weak
    """
    # Validate password strength
    is_valid, error_msg = validate_password_strength(request.password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    service = UserService()
    hashed_password = get_password_hash(request.password)
    user = await service.register_user(request.email, request.username, hashed_password, request.full_name)
    
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    usage = await service.get_api_usage(user.id)
    
    return UserResponse(
        user_id=str(user.id),
        email=user.email,
        username=user.username,
        is_anonymous=user.is_anonymous,
        preferences=user.preferences or {},
        cross_session_memory=user.cross_session_memory or {},
        api_usage=usage,
        created_at=user.created_at.isoformat()
    )


@router.post("/upgrade", response_model=UserResponse)
async def upgrade_anonymous_user(request: UpgradeRequest):
    """
    Upgrade anonymous user to registered.
    
    Preserves all existing sessions and data while adding email.
    
    Args:
        request: User ID, email, username and password
        
    Returns:
        UserResponse: Upgraded user details
        
    Raises:
        HTTPException: 400 if email exists, user not found, or password is weak
    """
    # Validate password strength
    is_valid, error_msg = validate_password_strength(request.password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    service = UserService()
    hashed_password = get_password_hash(request.password)
    user = await service.upgrade_anonymous_to_registered(
        uuid.UUID(request.user_id),
        request.email,
        request.username,
        hashed_password
    )
    
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Email already exists or user not found"
        )
    
    usage = await service.get_api_usage(user.id)
    
    return UserResponse(
        user_id=str(user.id),
        email=user.email,
        username=user.username,
        is_anonymous=user.is_anonymous,
        preferences=user.preferences or {},
        cross_session_memory=user.cross_session_memory or {},
        api_usage=usage,
        created_at=user.created_at.isoformat()
    )


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Get current user details.
    
    Returns:
        UserResponse: User details
        
    Raises:
        HTTPException: 404 if user not found
    """
    service = UserService()
    usage = await service.get_api_usage(current_user.id)
    
    return UserResponse(
        user_id=str(current_user.id),
        email=current_user.email,
        username=current_user.username,
        is_anonymous=current_user.is_anonymous,
        preferences=current_user.preferences or {},
        cross_session_memory=current_user.cross_session_memory or {},
        api_usage=usage,
        created_at=current_user.created_at.isoformat()
    )


@router.put("/me/preferences", response_model=UserResponse)
async def update_preferences(request: UpdatePreferencesRequest, current_user: User = Depends(get_current_user)):
    """
    Update user preferences.
    
    Args:
        request: Preferences to update
        
    Returns:
        UserResponse: Updated user details
        
    Raises:
        HTTPException: 404 if user not found
    """
    service = UserService()
    user = await service.update_preferences(
        current_user.id,
        request.preferences
    )
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    usage = await service.get_api_usage(user.id)
    
    return UserResponse(
        user_id=str(user.id),
        email=user.email,
        username=user.username,
        is_anonymous=user.is_anonymous,
        preferences=user.preferences or {},
        cross_session_memory=user.cross_session_memory or {},
        api_usage=usage,
        created_at=user.created_at.isoformat()
    )


@router.get("/me/sessions", response_model=List[SessionSummary])
async def get_user_sessions(limit: int = 10, current_user: User = Depends(get_current_user)):
    """
    Get user's conversation sessions.
    
    Args:
        limit: Maximum sessions to return (default: 10)
        
    Returns:
        List[SessionSummary]: List of session summaries
    """
    session_service = SessionService()
    sessions = await session_service.get_user_sessions(
        current_user.id,
        limit=limit
    )
    
    return [
        SessionSummary(
            session_id=str(s.id),
            is_complete=s.is_complete,
            created_at=s.created_at.isoformat(),
            updated_at=s.updated_at.isoformat(),
            message_count=len(s.session_data.get("history", []))
        )
        for s in sessions
    ]


@router.get("/me/usage")
async def get_api_usage(current_user: User = Depends(get_current_user)):
    """
    Get user's API usage statistics.
    
    Returns:
        dict: Usage statistics including limits and remaining calls
    """
    service = UserService()
    usage = await service.get_api_usage(current_user.id)
    
    if not usage:
        raise HTTPException(status_code=404, detail="User not found")
    
    return usage


@router.delete("/me")
async def delete_user_data(current_user: User = Depends(get_current_user)):
    """
    Delete all user data (GDPR compliance).
    
    Permanently deletes:
    - User account
    - All sessions
    - All chat messages
    - All saved results
    - Cross-session memory
    
    Returns:
        dict: Confirmation message
        
    Raises:
        HTTPException: 404 if user not found
    """
    service = UserService()
    deleted = await service.delete_user_data(current_user.id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "message": "All user data has been permanently deleted",
        "user_id": str(current_user.id)
    }
