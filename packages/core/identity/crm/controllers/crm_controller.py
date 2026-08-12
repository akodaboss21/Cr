"""
CRM Module - Controller with Search
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from uuid import uuid4
from datetime import datetime

from packages.core.database import get_db
from packages.core.security import get_current_user
from packages.core.identity.crm.models import CRM
from packages.core.identity.schemas import (
    CRMCreate, CRMUpdate, CRMResponse,
)

router = APIRouter(prefix="/crm", tags=["crm"])

# CRUD Handlers
async def create_crm(
    crm_create: CRMCreate,
    db: Session,
    current_user: dict
):
    """Create a new CRM entry"""
    db_crm = CRM(
        id=str(uuid4()),
        organization_id=current_user["organization_id"],
        name=crm_create.name,
        email=crm_create.email,
        phone=crm_create.phone,
        company=crm_create.company,
        source=crm_create.source,
        status=crm_create.status,
        score=crm_create.score,
        notes=crm_create.notes,
        tags=crm_create.tags,
        assigned_to=crm_create.assigned_to,
        pipeline_stage=crm_create.pipeline_stage,
        next_followup=crm_create.next_followup,
        first_interaction=datetime.utcnow(),
        last_interaction=datetime.utcnow(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(db_crm)
    db.commit()
    db.refresh(db_crm)
    return db_crm

async def get_crm(crm_id: str, db: Session, current_user: dict):
    """Retrieve a CRM entry by ID"""
    return db.query(CRM).filter(
        CRM.id == crm_id,
        CRM.organization_id == current_user["organization_id"]
    ).first()

async def update_crm(
    crm_id: str,
    crm_update: CRMUpdate,
    db: Session,
    current_user: dict
):
    """Update a CRM entry"""
    db_crm = await get_crm(crm_id, db, current_user)
    if not db_crm:
        return None
    
    for field, value in crm_update.dict(exclude_unset=True).items():
        setattr(db_crm, field, value)
    
    db_crm.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_crm)
    return db_crm

async def delete_crm(crm_id: str, db: Session, current_user: dict):
    """Delete a CRM entry"""
    db_crm = await get_crm(crm_id, db, current_user)
    if not db_crm:
        return False
    
    db.delete(db_crm)
    db.commit()
    return True

# REST Routes
@router.post("/", response_model=CRMResponse)
async def create_customer(
    crm_create: CRMCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new customer"""
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    db_crm = await create_crm(crm_create, db, current_user)
    return CRMResponse.from_orm(db_crm)

@router.get("/{crm_id}", response_model=CRMResponse)
async def get_customer(
    crm_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a customer"""
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    db_crm = await get_crm(crm_id, db, current_user)
    if not db_crm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    return CRMResponse.from_orm(db_crm)

@router.put("/{crm_id}", response_model=CRMResponse)
async def update_customer(
    crm_id: str,
    crm_update: CRMUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a customer"""
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    db_crm = await update_crm(crm_id, crm_update, db, current_user)
    if not db_crm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    return CRMResponse.from_orm(db_crm)

@router.delete("/{crm_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(
    crm_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a customer"""
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    deleted = await delete_crm(crm_id, db, current_user)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    return None

@router.get("/search", response_model=List[CRMResponse])
async def search_customers(
    query: str = Query(None, min_length=1, max_length=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Search for customers by name, email, phone, or notes."""
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    search_term = f"%{query}%"
    search_query = or_(
        func.lower(CRM.name).like(func.lower(search_term)),
        func.lower(CRM.email).like(func.lower(search_term)),
        func.lower(CRM.phone).like(func.lower(search_term)),
        func.lower(CRM.notes).like(func.lower(search_term)),
        func.lower(CRM.tags).like(func.lower(search_term)),
        func.lower(CRM.preferences).like(func.lower(search_term)),
    )
    
    results = db.query(CRM).filter(
        search_query,
        CRM.organization_id == current_user["organization_id"]
    ).all()
    
    return [CRMResponse.from_orm(result) for result in results]
