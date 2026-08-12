"""
Booking Module - Pydantic Schemas
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class BookingBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "pending"  # 'pending', 'confirmed', 'canceled', 'completed'
    start_time: datetime
    end_time: datetime
    timezone: str = "UTC"
    attendees: Optional[str] = None  # JSON array
    calendar_event_id: Optional[str] = None
    google_calendar_id: Optional[str] = None

class BookingCreate(BookingBase):
    pass

class BookingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    timezone: Optional[str] = None
    attendees: Optional[str] = None
    calendar_event_id: Optional[str] = None
    google_calendar_id: Optional[str] = None

class BookingResponse(BookingBase):
    id: str
    organization_id: str
    business_id: Optional[str] = None
    customer_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True