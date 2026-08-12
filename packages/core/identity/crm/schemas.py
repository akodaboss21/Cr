"""
CRM Module - Pydantic Schemas
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class CRMBase(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    source: Optional[str] = None  # 'website', 'phone', 'referral', etc.
    status: str = "lead"  # 'lead', 'customer', 'prospect', 'lost'
    score: int = 0
    notes: Optional[str] = None
    tags: Optional[str] = None  # JSON array
    assigned_to: Optional[str] = None
    pipeline_stage: Optional[str] = None
    next_followup: Optional[datetime] = None
    # Customer Profile Fields
    first_interaction: Optional[datetime] = None
    last_interaction: Optional[datetime] = None
    total_conversations: int = 0
    services_requested: Optional[str] = None  # JSON array
    bookings: Optional[str] = None  # JSON array
    # AI Memory
    preferences: Optional[str] = None  # JSON object
    notes_history: Optional[str] = None  # JSON array
    important_details: Optional[str] = None  # JSON object

class CRMCreate(CRMBase):
    pass

class CRMUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    source: Optional[str] = None
    status: Optional[str] = None
    score: Optional[int] = None
    notes: Optional[str] = None
    tags: Optional[str] = None
    assigned_to: Optional[str] = None
    pipeline_stage: Optional[str] = None
    next_followup: Optional[datetime] = None
    # Customer Profile Fields
    first_interaction: Optional[datetime] = None
    last_interaction: Optional[datetime] = None
    total_conversations: Optional[int] = None
    services_requested: Optional[str] = None
    bookings: Optional[str] = None
    # AI Memory
    preferences: Optional[str] = None
    notes_history: Optional[str] = None
    important_details: Optional[str] = None

class CRMResponse(CRMBase):
    id: str
    organization_id: str
    customer_id: Optional[str] = None
    business_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True