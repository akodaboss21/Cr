"""
Integration Module - Pydantic Schemas
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class IntegrationBase(BaseModel):
    name: str
    type: str  # 'google', 'meta', 'stripe', etc.
    config: Optional[str] = None  # JSON data
    is_active: bool = True

class IntegrationCreate(IntegrationBase):
    pass

class IntegrationUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    config: Optional[str] = None
    is_active: Optional[bool] = None
    last_sync: Optional[datetime] = None
    sync_status: Optional[str] = None

class IntegrationResponse(IntegrationBase):
    id: str
    organization_id: str
    last_sync: Optional[datetime] = None
    sync_status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True