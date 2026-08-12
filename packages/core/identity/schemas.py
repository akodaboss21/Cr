"""
Identity Module - Pydantic Schemas
"""
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

from packages.core.identity.ai_gateway.schemas import (
    AIProviderCreate,
    AIProviderUpdate,
    AIProviderResponse,
    PromptTemplateCreate,
    PromptTemplateUpdate,
    PromptTemplateResponse,
    AIUsageCreate,
    AIUsageResponse,
)
from packages.core.identity.background_workers.schemas import (
    BackgroundWorkerCreate,
    BackgroundWorkerUpdate,
    BackgroundWorkerResponse,
    BackgroundJobCreate,
    BackgroundJobUpdate,
    BackgroundJobResponse,
)
from packages.core.identity.booking.schemas import (
    BookingCreate,
    BookingUpdate,
    BookingResponse,
)
from packages.core.identity.business.schemas import (
    BusinessProfileCreate,
    BusinessProfileUpdate,
    BusinessProfileResponse,
)
from packages.core.identity.conversation.schemas import (
    MessageCreate,
    MessageResponse,
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
)
from packages.core.identity.crm.schemas import (
    CRMCreate,
    CRMUpdate,
    CRMResponse,
)
from packages.core.identity.integration.schemas import (
    IntegrationCreate,
    IntegrationUpdate,
    IntegrationResponse,
)
from packages.core.identity.knowledge.schemas import (
    KnowledgeCreate,
    KnowledgeUpdate,
    KnowledgeResponse,
)

BusinessProfileCreateSchema = BusinessProfileCreate
BusinessProfileUpdateSchema = BusinessProfileUpdate
BusinessProfileResponseSchema = BusinessProfileResponse

class SearchQuery(BaseModel):
    query: str

class SearchResult(BaseModel):
    id: str
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    score: Optional[float] = None

class UserBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(UserBase):
    id: str
    organization_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class OrganizationBase(BaseModel):
    name: str

class OrganizationCreate(OrganizationBase):
    pass

class OrganizationUpdate(BaseModel):
    name: Optional[str] = None

class OrganizationResponse(OrganizationBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Compatibility aliases used by the controllers and tests
OrganizationCreateSchema = OrganizationCreate
OrganizationUpdateSchema = OrganizationUpdate
OrganizationResponseSchema = OrganizationResponse

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[str] = None
    organization_id: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class AuditLogResponse(BaseModel):
    id: str
    organization_id: Optional[str] = None
    user_id: Optional[str] = None
    request_id: str
    event: str
    path: str
    method: str
    status_code: int
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    details: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

class InvitationCreate(BaseModel):
    email: EmailStr
    role: str

class InvitationResponse(BaseModel):
    id: str
    organization_id: str
    email: str
    role: str
    expires_at: datetime
    created_at: datetime
    used: bool
    
    class Config:
        from_attributes = True

class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

class RoleCreate(RoleBase):
    pass

class RoleResponse(RoleBase):
    id: int
    
    class Config:
        from_attributes = True

class PermissionBase(BaseModel):
    name: str
    description: Optional[str] = None

class PermissionCreate(PermissionBase):
    pass

class PermissionResponse(PermissionBase):
    id: int
    
    class Config:
        from_attributes = True