"""
Business Profile Module - Pydantic Schemas
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class BusinessProfileBase(BaseModel):
    business_name: str
    business_type: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    hours: Optional[str] = None
    services: Optional[str] = None
    pricing: Optional[str] = None
    staff_count: Optional[int] = None
    facebook: Optional[str] = None
    twitter: Optional[str] = None
    instagram: Optional[str] = None
    linkedin: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    cancellation_policy: Optional[str] = None
    privacy_policy: Optional[str] = None
    terms_of_service: Optional[str] = None

class BusinessProfileCreate(BusinessProfileBase):
    pass

class BusinessProfileUpdate(BaseModel):
    business_name: Optional[str] = None
    business_type: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    hours: Optional[str] = None
    services: Optional[str] = None
    pricing: Optional[str] = None
    staff_count: Optional[int] = None
    facebook: Optional[str] = None
    twitter: Optional[str] = None
    instagram: Optional[str] = None
    linkedin: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    cancellation_policy: Optional[str] = None
    privacy_policy: Optional[str] = None
    terms_of_service: Optional[str] = None

class BusinessProfileResponse(BusinessProfileBase):
    id: str
    organization_id: str
    owner_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True