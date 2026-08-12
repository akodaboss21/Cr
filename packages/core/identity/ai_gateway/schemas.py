"""
AI Gateway Module - Pydantic Schemas
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class AIProviderBase(BaseModel):
    name: str
    api_url: str
    api_key: Optional[str] = None
    model: Optional[str] = None
    is_active: bool = True

class AIProviderCreate(AIProviderBase):
    pass

class AIProviderUpdate(BaseModel):
    name: Optional[str] = None
    api_url: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None
    is_active: Optional[bool] = None

class AIProviderResponse(AIProviderBase):
    id: int
    organization_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class PromptTemplateBase(BaseModel):
    name: str
    description: Optional[str] = None
    template: str
    variables: Optional[str] = None  # JSON array
    category: Optional[str] = None
    version: str = "1.0"
    is_active: bool = True

class PromptTemplateCreate(PromptTemplateBase):
    pass

class PromptTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    template: Optional[str] = None
    variables: Optional[str] = None
    category: Optional[str] = None
    version: Optional[str] = None
    is_active: Optional[bool] = None

class PromptTemplateResponse(PromptTemplateBase):
    id: str
    organization_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class AIUsageBase(BaseModel):
    provider: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: Optional[str] = None
    request_id: Optional[str] = None
    response_time_ms: Optional[int] = None

class AIUsageCreate(AIUsageBase):
    pass

class AIUsageResponse(AIUsageBase):
    id: str
    organization_id: str
    conversation_id: Optional[str] = None
    created_at: datetime
    
    class Config:
        orm_mode = True