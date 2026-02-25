from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime


class ChatMessage(BaseModel):
    """Chat message model"""
    session_id: str
    sender: Literal["user", "bot"]
    message: str
    response_data: Optional[dict] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ChatSession(BaseModel):
    """Chat session model"""
    session_id: str
    store_id: int = 1
    user_id: Optional[int] = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity_at: datetime = Field(default_factory=datetime.utcnow)
    user_context: dict = Field(default_factory=dict)
    escalated: bool = False


class ChatResponse(BaseModel):
    """Structured chatbot response"""
    message: str
    product_cards: Optional[List[dict]] = None
    quick_replies: Optional[List[str]] = None
    action: Optional[Literal["add_to_cart", "checkout", "track_order", "escalate"]] = None
    action_data: Optional[dict] = None
    session_id: str


class ChatMessageRequest(BaseModel):
    """Request model for chat message"""
    message: str
    session_id: Optional[str] = None


class ChatSessionCreate(BaseModel):
    """Request model for creating a chat session"""
    user_id: Optional[int] = None
