"""
Conversation Module - Pydantic Schemas
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class MessageBase(BaseModel):
    content: str
    role: str  # 'user', 'assistant', 'system'
    timestamp: Optional[datetime] = None
    ai_provider: Optional[str] = None
    model: Optional[str] = None
    tokens_used: Optional[int] = None

class MessageCreate(MessageBase):
    pass

class MessageResponse(MessageBase):
    id: str
    conversation_id: str
    
    class Config:
        orm_mode = True

class ConversationBase(BaseModel):
    title: Optional[str] = None
    status: str = "active"  # 'active', 'closed', 'archived'
    channel: str = "web"  # 'web', 'mobile', 'api'
    ai_provider: Optional[str] = None
    model: Optional[str] = None

class ConversationCreate(ConversationBase):
    pass

class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    channel: Optional[str] = None
    ai_provider: Optional[str] = None
    model: Optional[str] = None

class ConversationResponse(ConversationBase):
    id: str
    organization_id: str
    business_id: Optional[str] = None
    participant_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_message_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True