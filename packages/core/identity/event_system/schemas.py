"""
Event System - Pydantic Schemas
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class EventBase(BaseModel):
    name: str
    event_type: str  # 'lead_created', 'appointment_scheduled', etc.
    description: Optional[str] = None
    is_active: bool = True

class EventCreate(EventBase):
    pass

class EventUpdate(BaseModel):
    name: Optional[str] = None
    event_type: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class EventResponse(EventBase):
    id: str
    organization_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class EventSubscriberBase(BaseModel):
    event_id: str
    user_id: Optional[str] = None
    organization_id: str
    role: Optional[str] = None
    notification_preferences: Optional[str] = None  # JSON data

class EventSubscriberCreate(EventSubscriberBase):
    pass

class EventSubscriberUpdate(BaseModel):
    event_id: Optional[str] = None
    user_id: Optional[str] = None
    organization_id: Optional[str] = None
    role: Optional[str] = None
    notification_preferences: Optional[str] = None

class EventSubscriberResponse(EventSubscriberBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class EventTriggerBase(BaseModel):
    event_id: str
    name: str
    condition: Optional[str] = None  # JSON data or simple expression
    action: str  # 'send_email', 'update_crm', etc.
    parameters: Optional[str] = None  # JSON data
    is_active: bool = True

class EventTriggerCreate(EventTriggerBase):
    pass

class EventTriggerUpdate(BaseModel):
    event_id: Optional[str] = None
    name: Optional[str] = None
    condition: Optional[str] = None
    action: Optional[str] = None
    parameters: Optional[str] = None
    is_active: Optional[bool] = None

class EventTriggerResponse(EventTriggerBase):
    id: str
    last_triggered_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True