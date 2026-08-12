"""
Knowledge Module - Pydantic Schemas
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class KnowledgeBase(BaseModel):
    title: str
    content: str
    content_type: Optional[str] = None  # 'text', 'pdf', 'html', 'url'
    source_url: Optional[str] = None
    tags: Optional[str] = None
    category: Optional[str] = None
    embedding_vector: Optional[str] = None  # JSON array
    processed: bool = False

class KnowledgeCreate(KnowledgeBase):
    pass

class KnowledgeUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    content_type: Optional[str] = None
    source_url: Optional[str] = None
    tags: Optional[str] = None
    category: Optional[str] = None
    embedding_vector: Optional[str] = None
    processed: Optional[bool] = None

class KnowledgeResponse(KnowledgeBase):
    id: str
    organization_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True