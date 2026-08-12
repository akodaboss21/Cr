"""
Background Workers Module - Controller
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime

from packages.core.database import get_db
from packages.core.security import get_current_user
from packages.core.identity.background_workers.models import BackgroundWorker, BackgroundJob
from packages.core.identity.schemas import (
    BackgroundWorkerCreate, BackgroundWorkerUpdate, BackgroundWorkerResponse,
    BackgroundJobCreate, BackgroundJobUpdate, BackgroundJobResponse
)

router = APIRouter(prefix="/background-workers", tags=["background-workers"])

# Background Worker endpoints
@router.post("/workers/", response_model=BackgroundWorkerResponse)
async def create_background_worker(
    worker_create: BackgroundWorkerCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new background worker"""
    # Verify user has permission to create background worker
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Create background worker
    db_worker = BackgroundWorker(
        id=str(uuid4()),
        organization_id=current_user["organization_id"],
        name=worker_create.name,
        type=worker_create.type,
        config=worker_create.config,
        is_active=worker_create.is_active,
        status=worker_create.status,
        tasks_processed=0,
        tasks_failed=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(db_worker)
    db.commit()
    db.refresh(db_worker)
    
    return BackgroundWorkerResponse.from_orm(db_worker)

@router.get("/workers/", response_model=List[BackgroundWorkerResponse])
async def get_background_workers(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """Get a list of background workers"""
    # Verify user has permission
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    workers = db.query(BackgroundWorker).filter(
        BackgroundWorker.organization_id == current_user["organization_id"]
    ).offset(skip).limit(limit).all()
    
    return [BackgroundWorkerResponse.from_orm(worker) for worker in workers]

@router.get("/workers/{worker_id}", response_model=BackgroundWorkerResponse)
async def get_background_worker(
    worker_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific background worker"""
    # Verify user has permission
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    worker = db.query(BackgroundWorker).filter(
        BackgroundWorker.id == worker_id,
        BackgroundWorker.organization_id == current_user["organization_id"]
    ).first()
    
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Background worker not found"
        )
    
    return BackgroundWorkerResponse.from_orm(worker)

@router.put("/workers/{worker_id}", response_model=BackgroundWorkerResponse)
async def update_background_worker(
    worker_id: str,
    worker_update: BackgroundWorkerUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a background worker"""
    # Verify user has permission
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    worker = db.query(BackgroundWorker).filter(
        BackgroundWorker.id == worker_id,
        BackgroundWorker.organization_id == current_user["organization_id"]
    ).first()
    
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Background worker not found"
        )
    
    # Update fields
    for field, value in worker_update.dict(exclude_unset=True).items():
        setattr(worker, field, value)
    
    worker.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(worker)
    
    return BackgroundWorkerResponse.from_orm(worker)

@router.delete("/workers/{worker_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_background_worker(
    worker_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a background worker"""
    # Verify user has permission
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    worker = db.query(BackgroundWorker).filter(
        BackgroundWorker.id == worker_id,
        BackgroundWorker.organization_id == current_user["organization_id"]
    ).first()
    
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Background worker not found"
        )
    
    db.delete(worker)
    db.commit()
    
    return None

# Background Job endpoints
@router.post("/jobs/", response_model=BackgroundJobResponse)
async def create_background_job(
    job_create: BackgroundJobCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new background job"""
    # Verify user has permission to create background job
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Create background job
    db_job = BackgroundJob(
        id=str(uuid4()),
        organization_id=current_user["organization_id"],
        worker_id=job_create.worker_id,
        task_type=job_create.task_type,
        task_data=job_create.task_data,
        status=job_create.status,
        retry_count=job_create.retry_count,
        max_retries=job_create.max_retries,
        scheduled_at=job_create.scheduled_at,
        started_at=job_create.started_at,
        completed_at=job_create.completed_at,
        result=job_create.result,
        error=job_create.error,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    
    return BackgroundJobResponse.from_orm(db_job)

@router.get("/jobs/", response_model=List[BackgroundJobResponse])
async def get_background_jobs(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """Get a list of background jobs"""
    # Verify user has permission
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    jobs = db.query(BackgroundJob).filter(
        BackgroundJob.organization_id == current_user["organization_id"]
    ).offset(skip).limit(limit).all()
    
    return [BackgroundJobResponse.from_orm(job) for job in jobs]

@router.get("/jobs/{job_id}", response_model=BackgroundJobResponse)
async def get_background_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific background job"""
    # Verify user has permission
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    job = db.query(BackgroundJob).filter(
        BackgroundJob.id == job_id,
        BackgroundJob.organization_id == current_user["organization_id"]
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Background job not found"
        )
    
    return BackgroundJobResponse.from_orm(job)

@router.put("/jobs/{job_id}", response_model=BackgroundJobResponse)
async def update_background_job(
    job_id: str,
    job_update: BackgroundJobUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a background job"""
    # Verify user has permission
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    job = db.query(BackgroundJob).filter(
        BackgroundJob.id == job_id,
        BackgroundJob.organization_id == current_user["organization_id"]
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Background job not found"
        )
    
    # Update fields
    for field, value in job_update.dict(exclude_unset=True).items():
        setattr(job, field, value)
    
    job.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(job)
    
    return BackgroundJobResponse.from_orm(job)

@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_background_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a background job"""
    # Verify user has permission
    if "organization_id" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    job = db.query(BackgroundJob).filter(
        BackgroundJob.id == job_id,
        BackgroundJob.organization_id == current_user["organization_id"]
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Background job not found"
        )
    
    db.delete(job)
    db.commit()
    
    return None