"""
Organizations Module - Controller
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime

from packages.core.database import get_db
from packages.core.identity.models import Organization, User
from packages.core.identity.business.models import BusinessProfile
from packages.core.identity.billing.models import Subscription
from packages.core.identity.schemas import OrganizationCreateSchema, OrganizationUpdateSchema, OrganizationResponseSchema
from packages.core.security import get_current_user

router = APIRouter(tags=["organizations"])

@router.post("/", response_model=OrganizationResponseSchema)
async def create_organization(
    org_create: OrganizationCreateSchema,
    db: Session = Depends(get_db)
):
    """Create a new organization"""
    # Check if organization name already exists
    existing_org = db.query(Organization).filter(Organization.name == org_create.name).first()
    if existing_org:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization with this name already exists"
        )
    
    # Create new organization
    db_org = Organization(
        id=str(uuid4()),
        name=org_create.name,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(db_org)
    db.commit()
    db.refresh(db_org)
    
    return OrganizationResponseSchema.from_orm(db_org)

@router.get("/", response_model=List[OrganizationResponseSchema])
async def get_organizations(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """Get a list of organizations with pagination"""
    if current_user.get("is_admin", False):
        organizations = db.query(Organization).offset(skip).limit(limit).all()
    else:
        organizations = db.query(Organization).filter(
            Organization.id == current_user["organization_id"]
        ).offset(skip).limit(limit).all()
    return [OrganizationResponseSchema.from_orm(org) for org in organizations]

@router.get("/{org_id}", response_model=OrganizationResponseSchema)
async def get_organization(
    org_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get an organization by ID"""
    if not current_user.get("is_admin", False) and org_id != current_user["organization_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )
    organization = db.query(Organization).filter(Organization.id == org_id).first()
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    return OrganizationResponseSchema.from_orm(organization)

@router.put("/{org_id}", response_model=OrganizationResponseSchema)
async def update_organization(
    org_id: str,
    org_update: OrganizationUpdateSchema,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update an organization by ID"""
    if not current_user.get("is_admin", False) and org_id != current_user["organization_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )
    organization = db.query(Organization).filter(Organization.id == org_id).first()
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Update fields
    for field, value in org_update.dict(exclude_unset=True).items():
        setattr(organization, field, value)
    
    organization.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(organization)
    
    return OrganizationResponseSchema.from_orm(organization)

@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    org_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete an organization by ID"""
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    organization = db.query(Organization).filter(Organization.id == org_id).first()
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    db.delete(organization)
    db.commit()
    
    return None

@router.get("/{org_id}/details", response_model=dict)
async def get_organization_details(
    org_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get detailed information about an organization"""
    if not current_user.get("is_admin", False) and org_id != current_user["organization_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )
    organization = db.query(Organization).filter(Organization.id == org_id).first()
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    user_count = db.query(User).filter(User.organization_id == org_id).count()
    business_count = db.query(BusinessProfile).filter(BusinessProfile.organization_id == org_id).count()
    subscription_count = db.query(Subscription).filter(Subscription.organization_id == org_id).count()
    
    return {
        "id": organization.id,
        "name": organization.name,
        "created_at": organization.created_at,
        "updated_at": organization.updated_at,
        "user_count": user_count,
        "business_count": business_count,
        "subscription_count": subscription_count
    }