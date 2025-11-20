from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = datetime.now()

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    conversation_history: List[ChatMessage] = []

class ChatResponse(BaseModel):
    message: str
    session_id: str
    is_complete: bool = False
    user_profile: Optional[Dict[str, Any]] = None
    suggested_actions: Optional[List[str]] = None  # Quick reply buttons for frontend