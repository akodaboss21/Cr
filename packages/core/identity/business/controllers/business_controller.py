"""
Business Profile Module - Controller
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime
import jwt

from packages.core.config import settings
from packages.core.database import get_db
from packages.core.identity.business.models import BusinessProfile
from packages.core.identity.models import User
from packages.core.identity.schemas import BusinessProfileCreateSchema, BusinessProfileUpdateSchema, BusinessProfileResponseSchema
from packages.core.identity.conversation.models import Conversation
from packages.core.security import decode_token, get_current_user

router = APIRouter(prefix="/business-profiles", tags=["business-profiles"])

@router.post("/", response_model=BusinessProfileResponseSchema)
async def create_business_profile(
    bp_create: BusinessProfileCreateSchema,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new business profile"""
    # Verify user has permission to create business profile
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Check if business profile already exists for this organization
    existing_bp = db.query(BusinessProfile).filter(
        BusinessProfile.organization_id == current_user["organization_id"]
    ).first()
    
    if existing_bp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Business profile already exists for this organization"
        )
    
    # Create business profile
    db_bp = BusinessProfile(
        id=str(uuid4()),
        organization_id=current_user["organization_id"],
        owner_id=current_user["user_id"],
        business_name=bp_create.business_name,
        business_type=bp_create.business_type,
        address=bp_create.address,
        phone=bp_create.phone,
        email=bp_create.email,
        website=bp_create.website,
        hours=bp_create.hours,
        services=bp_create.services,
        pricing=bp_create.pricing,
        staff_count=bp_create.staff_count,
        facebook=bp_create.facebook,
        twitter=bp_create.twitter,
        instagram=bp_create.instagram,
        linkedin=bp_create.linkedin,
        logo_url=bp_create.logo_url,
        primary_color=bp_create.primary_color,
        secondary_color=bp_create.secondary_color,
        cancellation_policy=bp_create.cancellation_policy,
        privacy_policy=bp_create.privacy_policy,
        terms_of_service=bp_create.terms_of_service,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(db_bp)
    db.commit()
    db.refresh(db_bp)
    
    return BusinessProfileResponseSchema.from_orm(db_bp)

@router.get("/", response_model=List[BusinessProfileResponseSchema])
async def get_business_profiles(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """Get a list of business profiles with pagination"""
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    business_profiles = db.query(BusinessProfile).filter(
        BusinessProfile.organization_id == current_user["organization_id"]
    ).offset(skip).limit(limit).all()
    return [BusinessProfileResponseSchema.from_orm(bp) for bp in business_profiles]

def _resolve_widget_or_user_access(request: Request, db: Session) -> Dict[str, Any]:
    auth_header = request.headers.get("authorization", "") or request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
        claims = decode_token(token)
        if claims.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        user_id = claims.get("sub")
        organization_id = claims.get("org_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
        user = db.get(User, user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        return {
            "type": "user",
            "organization_id": organization_id,
        }

    header_api_key = request.headers.get("x-widget-api-key") or request.headers.get("X-Widget-Api-Key")
    if header_api_key:
        if settings.WIDGET_API_KEY and header_api_key == settings.WIDGET_API_KEY:
            return {"type": "widget_api_key"}
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid widget API key")

    header_token = request.headers.get("x-widget-token") or request.headers.get("X-Widget-Token")
    if header_token:
        try:
            secret = settings.WIDGET_SIGNING_SECRET or settings.SECRET_KEY
            claims = jwt.decode(header_token, secret, algorithms=["HS256"])
            return {
                "type": "widget_token",
                "organization_id": claims.get("organization_id"),
                "business_id": claims.get("business_id"),
                "customer_id": claims.get("customer_id"),
            }
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid widget token") from exc

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required"
    )


@router.get("/{bp_id}", response_model=BusinessProfileResponseSchema)
async def get_business_profile(
    bp_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Get a business profile by ID"""
    auth_context = _resolve_widget_or_user_access(request, db)
    business_profile = db.query(BusinessProfile).filter(
        BusinessProfile.id == bp_id
    ).first()
    if not business_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found"
        )

    if auth_context["type"] == "user":
        if business_profile.organization_id != auth_context["organization_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

    if auth_context["type"] == "widget_token":
        if auth_context.get("business_id") and auth_context["business_id"] != bp_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Widget token does not grant access to this business profile"
            )
        if auth_context.get("organization_id") and business_profile.organization_id != auth_context["organization_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

    return BusinessProfileResponseSchema.from_orm(business_profile)

@router.put("/{bp_id}", response_model=BusinessProfileResponseSchema)
async def update_business_profile(
    bp_id: str,
    bp_update: BusinessProfileUpdateSchema,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a business profile by ID"""
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    business_profile = db.query(BusinessProfile).filter(
        BusinessProfile.id == bp_id,
        BusinessProfile.organization_id == current_user["organization_id"]
    ).first()
    
    if not business_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found"
        )
    
    # Verify ownership
    if business_profile.owner_id != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )
    
    # Update fields
    for field, value in bp_update.dict(exclude_unset=True).items():
        setattr(business_profile, field, value)
    
    business_profile.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(business_profile)
    
    return BusinessProfileResponseSchema.from_orm(business_profile)

@router.delete("/{bp_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_business_profile(
    bp_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a business profile by ID"""
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    business_profile = db.query(BusinessProfile).filter(
        BusinessProfile.id == bp_id,
        BusinessProfile.organization_id == current_user["organization_id"]
    ).first()
    
    if not business_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found"
        )
    
    # Verify ownership
    if business_profile.owner_id != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )
    
    db.delete(business_profile)
    db.commit()
    
    return None

@router.get("/{bp_id}/details", response_model=dict)
async def get_business_profile_details(
    bp_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get detailed information about a business profile"""
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    business_profile = db.query(BusinessProfile).filter(
        BusinessProfile.id == bp_id,
        BusinessProfile.organization_id == current_user["organization_id"]
    ).first()
    if not business_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found"
        )
    
    organization_id = business_profile.organization_id
    user_count = db.query(User).filter(User.organization_id == organization_id).count()
    conversation_count = db.query(Conversation).filter(
        Conversation.business_id == bp_id,
        Conversation.organization_id == current_user["organization_id"]
    ).count()
    
    return {
        "id": business_profile.id,
        "organization_id": business_profile.organization_id,
        "owner_id": business_profile.owner_id,
        "business_name": business_profile.business_name,
        "business_type": business_profile.business_type,
        "address": business_profile.address,
        "phone": business_profile.phone,
        "email": business_profile.email,
        "website": business_profile.website,
        "hours": business_profile.hours,
        "services": business_profile.services,
        "pricing": business_profile.pricing,
        "staff_count": business_profile.staff_count,
        "facebook": business_profile.facebook,
        "twitter": business_profile.twitter,
        "instagram": business_profile.instagram,
        "linkedin": business_profile.linkedin,
        "logo_url": business_profile.logo_url,
        "primary_color": business_profile.primary_color,
        "secondary_color": business_profile.secondary_color,
        "cancellation_policy": business_profile.cancellation_policy,
        "privacy_policy": business_profile.privacy_policy,
        "terms_of_service": business_profile.terms_of_service,
        "created_at": business_profile.created_at,
        "updated_at": business_profile.updated_at,
        "user_count": user_count,
        "conversation_count": conversation_count
    }