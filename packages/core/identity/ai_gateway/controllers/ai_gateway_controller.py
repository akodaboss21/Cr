"""
AI Gateway Module - Controller
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime

from packages.core.database import get_db
from packages.core.security import get_current_user
from packages.core.identity.ai_gateway.models import AIProvider, PromptTemplate, AIUsage
from packages.core.identity.schemas import (
    AIProviderCreate, AIProviderUpdate, AIProviderResponse,
    PromptTemplateCreate, PromptTemplateUpdate, PromptTemplateResponse,
    AIUsageCreate, AIUsageResponse
)

router = APIRouter(prefix="/ai", tags=["ai"])

# AI Provider endpoints
@router.post("/providers/", response_model=AIProviderResponse)
async def create_ai_provider(
    provider_create: AIProviderCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new AI provider"""
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    db_provider = AIProvider(
        organization_id=current_user["organization_id"],
        name=provider_create.name,
        api_url=provider_create.api_url,
        api_key=provider_create.api_key,
        model=provider_create.model,
        is_active=provider_create.is_active,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(db_provider)
    db.commit()
    db.refresh(db_provider)
    
    return AIProviderResponse.from_orm(db_provider)

@router.get("/providers/", response_model=List[AIProviderResponse])
async def get_ai_providers(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """Get a list of AI providers"""
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    providers = db.query(AIProvider).filter(
        AIProvider.organization_id == current_user["organization_id"]
    ).offset(skip).limit(limit).all()
    return [AIProviderResponse.from_orm(provider) for provider in providers]

@router.get("/providers/{provider_id}", response_model=AIProviderResponse)
async def get_ai_provider(
    provider_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific AI provider"""
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    provider = db.query(AIProvider).filter(
        AIProvider.id == provider_id,
        AIProvider.organization_id == current_user["organization_id"]
    ).first()
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI provider not found"
        )
    
    return AIProviderResponse.from_orm(provider)

@router.put("/providers/{provider_id}", response_model=AIProviderResponse)
async def update_ai_provider(
    provider_id: int,
    provider_update: AIProviderUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update an AI provider"""
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    provider = db.query(AIProvider).filter(
        AIProvider.id == provider_id,
        AIProvider.organization_id == current_user["organization_id"]
    ).first()
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI provider not found"
        )
    
    for field, value in provider_update.dict(exclude_unset=True).items():
        setattr(provider, field, value)
    
    provider.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(provider)
    
    return AIProviderResponse.from_orm(provider)

@router.delete("/providers/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ai_provider(
    provider_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete an AI provider"""
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    provider = db.query(AIProvider).filter(
        AIProvider.id == provider_id,
        AIProvider.organization_id == current_user["organization_id"]
    ).first()
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI provider not found"
        )
    
    db.delete(provider)
    db.commit()
    
    return None

# Prompt Template endpoints
@router.post("/prompt-templates/", response_model=PromptTemplateResponse)
async def create_prompt_template(
    template_create: PromptTemplateCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new prompt template"""
    # Verify user has permission to create prompt template
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Create prompt template
    db_template = PromptTemplate(
        id=str(uuid4()),
        organization_id=current_user["organization_id"],
        name=template_create.name,
        description=template_create.description,
        template=template_create.template,
        variables=template_create.variables,
        category=template_create.category,
        version=template_create.version,
        is_active=template_create.is_active,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    
    return PromptTemplateResponse.from_orm(db_template)

@router.get("/prompt-templates/", response_model=List[PromptTemplateResponse])
async def get_prompt_templates(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """Get a list of prompt templates"""
    # Verify user has permission
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    templates = db.query(PromptTemplate).filter(
        PromptTemplate.organization_id == current_user["organization_id"]
    ).offset(skip).limit(limit).all()
    
    return [PromptTemplateResponse.from_orm(template) for template in templates]

@router.get("/prompt-templates/{template_id}", response_model=PromptTemplateResponse)
async def get_prompt_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific prompt template"""
    # Verify user has permission
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    template = db.query(PromptTemplate).filter(
        PromptTemplate.id == template_id,
        PromptTemplate.organization_id == current_user["organization_id"]
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt template not found"
        )
    
    return PromptTemplateResponse.from_orm(template)

@router.put("/prompt-templates/{template_id}", response_model=PromptTemplateResponse)
async def update_prompt_template(
    template_id: str,
    template_update: PromptTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a prompt template"""
    # Verify user has permission
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    template = db.query(PromptTemplate).filter(
        PromptTemplate.id == template_id,
        PromptTemplate.organization_id == current_user["organization_id"]
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt template not found"
        )
    
    # Update fields
    for field, value in template_update.dict(exclude_unset=True).items():
        setattr(template, field, value)
    
    template.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(template)
    
    return PromptTemplateResponse.from_orm(template)

@router.delete("/prompt-templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prompt_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a prompt template"""
    # Verify user has permission
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    template = db.query(PromptTemplate).filter(
        PromptTemplate.id == template_id,
        PromptTemplate.organization_id == current_user["organization_id"]
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt template not found"
        )
    
    db.delete(template)
    db.commit()
    
    return None

# AI Usage endpoints
@router.post("/usage/", response_model=AIUsageResponse)
async def create_ai_usage(
    usage_create: AIUsageCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new AI usage record"""
    # Verify user has permission to create AI usage
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Create AI usage record
    db_usage = AIUsage(
        id=str(uuid4()),
        organization_id=current_user["organization_id"],
        conversation_id=usage_create.conversation_id,
        provider=usage_create.provider,
        model=usage_create.model,
        prompt_tokens=usage_create.prompt_tokens,
        completion_tokens=usage_create.completion_tokens,
        total_tokens=usage_create.total_tokens,
        cost_usd=usage_create.cost_usd,
        request_id=usage_create.request_id,
        response_time_ms=usage_create.response_time_ms,
        created_at=datetime.utcnow()
    )
    
    db.add(db_usage)
    db.commit()
    db.refresh(db_usage)
    
    return AIUsageResponse.from_orm(db_usage)

@router.get("/usage/", response_model=List[AIUsageResponse])
async def get_ai_usage(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """Get a list of AI usage records"""
    # Verify user has permission
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    usage_records = db.query(AIUsage).filter(
        AIUsage.organization_id == current_user["organization_id"]
    ).offset(skip).limit(limit).all()
    
    return [AIUsageResponse.from_orm(usage) for usage in usage_records]

@router.get("/usage/{usage_id}", response_model=AIUsageResponse)
async def get_ai_usage_record(
    usage_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific AI usage record"""
    # Verify user has permission
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    usage = db.query(AIUsage).filter(
        AIUsage.id == usage_id,
        AIUsage.organization_id == current_user["organization_id"]
    ).first()
    
    if not usage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI usage record not found"
        )
    
    return AIUsageResponse.from_orm(usage)