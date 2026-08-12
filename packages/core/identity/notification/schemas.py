"""
Notification Module - Pydantic Schemas
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class NotificationBase(BaseModel):
    title: str
    message: str
    type: str  # 'email', 'sms', 'push', 'webhook'
    recipient: Optional[str] = None
    data: Optional[str] = None  # JSON data

class NotificationCreate(NotificationBase):
    pass

class NotificationUpdate(BaseModel):
    title: Optional[str] = None
    message: Optional[str] = None
    type: Optional[str] = None
    recipient: Optional[str] = None
    status: Optional[str] = None
    data: Optional[str] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None

class NotificationResponse(NotificationBase):
    id: str
    organization_id: str
    business_id: Optional[str] = None
    recipient_id: str
    status: str
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True


class NotificationSettingBase(BaseModel):
    business_id: Optional[str] = None
    event_type: str
    enabled: bool = True
    channels: Optional[str] = None
    schedule: Optional[str] = None
    timezone: str = "UTC"
    data: Optional[str] = None


class NotificationSettingCreate(NotificationSettingBase):
    pass


class NotificationSettingUpdate(BaseModel):
    business_id: Optional[str] = None
    event_type: Optional[str] = None
    enabled: Optional[bool] = None
    channels: Optional[str] = None
    schedule: Optional[str] = None
    timezone: Optional[str] = None
    data: Optional[str] = None


class NotificationSettingResponse(NotificationSettingBase):
    id: str
    organization_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class NotificationDispatchRequest(BaseModel):
    event_type: str
    recipient: dict
    payload: Optional[dict] = None
    channels: Optional[List[str]] = None


class NotificationDispatchResponse(BaseModel):
    results: List[dict]