from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from packages.core.database import get_db
from packages.core.security import get_current_user, get_password_hash
from packages.core.identity.models import User
from packages.core.identity.schemas import UserCreate, UserUpdate, UserResponse
from packages.core.supabase_client import get_supabase_client, get_supabase_admin_client

router = APIRouter(tags=["users"])

# Supabase client initialization
supabase_client = get_supabase_client()
supabase_admin_client = get_supabase_admin_client()

# User endpoints
@router.post("/", response_model=UserResponse)
async def create_user(
    user_create: UserCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new user with Supabase integration"""
    # Verify admin privileges
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )

    # Create user in Supabase
    try:
        supabase_admin_client = get_supabase_admin_client()
        if not supabase_admin_client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase admin client not available"
            )
        supabase_response = supabase_admin_client.auth.admin.create_user(
            email=user_create.email,
            password=user_create.password,
            options={"email": user_create.email}
        )
        # Create user in local database
        db_user = User(
            id=str(uuid.uuid4()),
            organization_id=current_user["organization_id"],
            email=user_create.email,
            hashed_password=get_password_hash(user_create.password),
            first_name=user_create.first_name,
            last_name=user_create.last_name,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return UserResponse.from_orm(db_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"User creation failed: {str(e)}"
        )

# User update endpoint
@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update an existing user"""
    # Verify admin privileges
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )

    # Update user in Supabase
    try:
        supabase_admin_client = get_supabase_admin_client()
        if not supabase_admin_client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase admin client not available"
            )
        # Update user in local database
        db_user = db.query(User).filter(
            User.id == user_id,
            User.organization_id == current_user["organization_id"]
        ).first()
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        update_payload = user_update.dict(exclude_unset=True)
        if update_payload.get("email"):
            db_user.email = update_payload["email"]
        if update_payload.get("first_name") is not None:
            db_user.first_name = update_payload["first_name"]
        if update_payload.get("last_name") is not None:
            db_user.last_name = update_payload["last_name"]
        if update_payload.get("is_active") is not None:
            db_user.is_active = update_payload["is_active"]
        if update_payload.get("password"):
            db_user.hashed_password = get_password_hash(update_payload["password"])

        db_user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_user)
        return UserResponse.from_orm(db_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"User update failed: {str(e)}"
        )

# User deletion endpoint
@router.delete("/{user_id}", response_model=UserResponse)
async def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a user"""
    # Verify admin privileges
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )

    # Delete user from Supabase
    try:
        supabase_admin_client = get_supabase_admin_client()
        if not supabase_admin_client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Supabase admin client not available"
            )
        supabase_response = supabase_admin_client.auth.admin.delete_user(
            user_id=user_id
        )
        # Delete user from local database
        db_user = db.query(User).filter(
            User.id == user_id,
            User.organization_id == current_user["organization_id"]
        ).first()
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        response_data = UserResponse.from_orm(db_user)
        db.delete(db_user)
        db.commit()
        return response_data
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"User deletion failed: {str(e)}"
        )