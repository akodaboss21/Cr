"""
Integration Module - Controller
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime

from packages.core.database import get_db
from packages.core.security import get_current_user
from packages.core.identity.integration.models import Integration
from packages.core.identity.schemas import (
    IntegrationCreate, IntegrationUpdate, IntegrationResponse
)

router = APIRouter(prefix="/integrations", tags=["integrations"])

@router.post("/", response_model=IntegrationResponse)
async def create_integration(
    integration_create: IntegrationCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new integration"""
    # Verify user has permission to create integration
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Create integration
    db_integration = Integration(
        id=str(uuid4()),
        organization_id=current_user["organization_id"],
        name=integration_create.name,
        type=integration_create.type,
        config=integration_create.config,
        is_active=integration_create.is_active,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(db_integration)
    db.commit()
    db.refresh(db_integration)
    
    return IntegrationResponse.from_orm(db_integration)

@router.get("/", response_model=List[IntegrationResponse])
async def get_integrations(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """Get a list of integrations"""
    # Verify user has permission
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    integrations = db.query(Integration).filter(
        Integration.organization_id == current_user["organization_id"]
    ).offset(skip).limit(limit).all()
    
    return [IntegrationResponse.from_orm(integration) for integration in integrations]

@router.get("/{integration_id}", response_model=IntegrationResponse)
async def get_integration(
    integration_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific integration"""
    # Verify user has permission
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    integration = db.query(Integration).filter(
        Integration.id == integration_id,
        Integration.organization_id == current_user["organization_id"]
    ).first()
    
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found"
        )
    
    return IntegrationResponse.from_orm(integration)

@router.put("/{integration_id}", response_model=IntegrationResponse)
async def update_integration(
    integration_id: str,
    integration_update: IntegrationUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update an integration"""
    # Verify user has permission
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    integration = db.query(Integration).filter(
        Integration.id == integration_id,
        Integration.organization_id == current_user["organization_id"]
    ).first()
    
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found"
        )
    
    # Update fields
    for field, value in integration_update.dict(exclude_unset=True).items():
        setattr(integration, field, value)
    
    integration.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(integration)
    
    return IntegrationResponse.from_orm(integration)

@router.delete("/{integration_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_integration(
    integration_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete an integration"""
    # Verify user has permission
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    integration = db.query(Integration).filter(
        Integration.id == integration_id,
        Integration.organization_id == current_user["organization_id"]
    ).first()
    
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found"
        )
    
    db.delete(integration)
    db.commit()
    
    return None