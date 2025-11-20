
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from sqlalchemy import select
from app.db.models import User
import uuid

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/token")

def verify_password(plain_password, hashed_password):
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)

def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password meets security requirements.
    
    Requirements:
    - At least 8 characters
    - Contains at least one uppercase letter
    - Contains at least one lowercase letter
    - Contains at least one digit
    
    Returns:
        tuple[bool, str]: (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"
    return True, ""

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """Create a JWT access token with expiration."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Validate JWT token and return the current user from database.
    
    Args:
        token: JWT token from Authorization header
        
    Returns:
        User: The authenticated user object
        
    Raises:
        HTTPException: 401 if token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Fetch user from database to ensure they still exist and are valid
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.id == uuid.UUID(user_id))
        )
        user = result.scalar_one_or_none()
        
        if user is None:
            raise credentials_exception
        
        return user
