"""
Organizations Module - Pydantic Schemas
"""
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID

class OrganizationBase(BaseModel):
    name: str
    description: Optional[str] = None

class OrganizationCreate(OrganizationBase):
    pass

class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class OrganizationResponse(OrganizationBase):
    id: str
    created_at: str
    updated_at: str
    
    class Config:
        orm_mode = True